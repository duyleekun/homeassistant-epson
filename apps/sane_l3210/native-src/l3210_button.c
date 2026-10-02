#include <libusb-1.0/libusb.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

#define EPSON_VID 0x04b8
#define L3210_PID 0x1188

static volatile sig_atomic_t running = 1;

static void stop_running(int signal_number) {
    (void)signal_number;
    running = 0;
}

static int find_scanner_interface(
    libusb_device_handle *handle,
    int *interface_number,
    unsigned char *endpoint_in,
    unsigned char *endpoint_out
) {
    libusb_device *device = libusb_get_device(handle);
    struct libusb_config_descriptor *config = NULL;
    int result = libusb_get_active_config_descriptor(device, &config);
    if (result != 0) {
        return result;
    }

    result = LIBUSB_ERROR_NOT_FOUND;
    for (int i = 0; i < config->bNumInterfaces; ++i) {
        const struct libusb_interface *interface = &config->interface[i];
        for (int a = 0; a < interface->num_altsetting; ++a) {
            const struct libusb_interface_descriptor *alt = &interface->altsetting[a];
            unsigned char in = 0;
            unsigned char out = 0;
            for (int e = 0; e < alt->bNumEndpoints; ++e) {
                const struct libusb_endpoint_descriptor *endpoint = &alt->endpoint[e];
                if ((endpoint->bmAttributes & LIBUSB_TRANSFER_TYPE_MASK) != LIBUSB_TRANSFER_TYPE_BULK) {
                    continue;
                }
                if (endpoint->bEndpointAddress & LIBUSB_ENDPOINT_IN) {
                    in = endpoint->bEndpointAddress;
                } else {
                    out = endpoint->bEndpointAddress;
                }
            }
            if (alt->bInterfaceClass == LIBUSB_CLASS_VENDOR_SPEC && in && out) {
                *interface_number = alt->bInterfaceNumber;
                *endpoint_in = in;
                *endpoint_out = out;
                result = 0;
                goto done;
            }
        }
    }

done:
    libusb_free_config_descriptor(config);
    return result;
}

static libusb_device_handle *open_scanner(
    libusb_context *context,
    int *interface_number,
    unsigned char *endpoint_in,
    unsigned char *endpoint_out
) {
    libusb_device_handle *handle = libusb_open_device_with_vid_pid(context, EPSON_VID, L3210_PID);
    if (!handle) {
        return NULL;
    }
    if (find_scanner_interface(handle, interface_number, endpoint_in, endpoint_out) != 0) {
        libusb_close(handle);
        return NULL;
    }
    libusb_set_auto_detach_kernel_driver(handle, 1);
    if (libusb_claim_interface(handle, *interface_number) != 0) {
        libusb_close(handle);
        return NULL;
    }
    return handle;
}

static int button_status(
    libusb_device_handle *handle,
    unsigned char endpoint_in,
    unsigned char endpoint_out,
    unsigned char *status
) {
    unsigned char command[] = {0x1b, '!'};
    unsigned char header[4] = {0};
    unsigned char data[256] = {0};
    int transferred = 0;

    int result = libusb_bulk_transfer(handle, endpoint_out, command, sizeof(command), &transferred, 1500);
    if (result != 0 || transferred != (int)sizeof(command)) {
        return result ? result : LIBUSB_ERROR_IO;
    }
    result = libusb_bulk_transfer(handle, endpoint_in, header, sizeof(header), &transferred, 1500);
    if (result != 0 || transferred != (int)sizeof(header) || header[0] != 0x02) {
        return result ? result : LIBUSB_ERROR_IO;
    }

    unsigned int length = (unsigned int)header[2] | ((unsigned int)header[3] << 8);
    if (length == 0 || length > sizeof(data)) {
        return LIBUSB_ERROR_OVERFLOW;
    }
    result = libusb_bulk_transfer(handle, endpoint_in, data, (int)length, &transferred, 1500);
    if (result != 0 || transferred != (int)length) {
        return result ? result : LIBUSB_ERROR_IO;
    }
    *status = data[0];
    return 0;
}

static int initialize_scanner(
    libusb_device_handle *handle,
    unsigned char endpoint_in,
    unsigned char endpoint_out
) {
    unsigned char command[] = {0x1b, '@'};
    unsigned char ack = 0;
    int transferred = 0;

    int result = libusb_bulk_transfer(handle, endpoint_out, command, sizeof(command), &transferred, 1500);
    if (result != 0 || transferred != (int)sizeof(command)) {
        fprintf(stderr, "L3210 ESC @ write: result=%s bytes=%d\n", libusb_error_name(result), transferred);
        return result ? result : LIBUSB_ERROR_IO;
    }
    /* ESC @ returns one ACK byte, unlike the framed ESC ! response. */
    result = libusb_bulk_transfer(handle, endpoint_in, &ack, 1, &transferred, 1500);
    fprintf(stderr, "L3210 ESC @ reply: result=%s bytes=%d value=0x%02x\n",
            libusb_error_name(result), transferred, ack);
    if (result != 0 || transferred != 1 || ack != 0x06) {
        return result ? result : LIBUSB_ERROR_IO;
    }
    return 0;
}

static int release_scanner(
    libusb_device_handle *handle,
    unsigned char endpoint_in,
    unsigned char endpoint_out
) {
    unsigned char command[] = {0x1b, ')'};
    unsigned char ack = 0;
    int transferred = 0;

    int result = libusb_bulk_transfer(handle, endpoint_out, command, sizeof(command), &transferred, 1500);
    if (result != 0 || transferred != (int)sizeof(command)) {
        return result ? result : LIBUSB_ERROR_IO;
    }
    result = libusb_bulk_transfer(handle, endpoint_in, &ack, 1, &transferred, 1500);
    if (result != 0 || transferred != 1 || ack != 0x80) {
        return result ? result : LIBUSB_ERROR_IO;
    }
    return 0;
}

static void run_action(const char *program, unsigned char button) {
    char button_text[16];
    snprintf(button_text, sizeof(button_text), "%u", button);
    pid_t child = fork();
    if (child == 0) {
        setenv("ES2_BUTTON_NUM", button_text, 1);
        execl(program, program, (char *)NULL);
        perror("exec panel scan action");
        _exit(127);
    }
    if (child > 0) {
        int status = 0;
        waitpid(child, &status, 0);
        fprintf(stderr, "Panel scan action exit=%d\n",
                WIFEXITED(status) ? WEXITSTATUS(status) : -1);
    }
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s ACTION\n", argv[0]);
        return 2;
    }
    signal(SIGINT, stop_running);
    signal(SIGTERM, stop_running);

    libusb_context *context = NULL;
    if (libusb_init(&context) != 0) {
        return 1;
    }
    fprintf(stderr, "L3210 button listener ready\n");

    unsigned char previous_status = 0;
    int needs_initialize = 1;
    libusb_device_handle *handle = NULL;
    int interface_number = -1;
    unsigned char endpoint_in = 0;
    unsigned char endpoint_out = 0;

    while (running) {
        if (handle == NULL) {
            handle = open_scanner(context, &interface_number, &endpoint_in, &endpoint_out);
        }
        if (!handle) {
            sleep(1);
            continue;
        }

        if (needs_initialize) {
            needs_initialize = 0;
            int reset_result = initialize_scanner(handle, endpoint_in, endpoint_out);
            fprintf(stderr, "L3210 session initialize: %s\n", libusb_error_name(reset_result));
            int release_result = release_scanner(handle, endpoint_in, endpoint_out);
            fprintf(stderr, "L3210 session release: %s\n", libusb_error_name(release_result));
            libusb_release_interface(handle, interface_number);
            libusb_close(handle);
            handle = NULL;
            continue;
        }

        unsigned char status = 0;
        int result = button_status(handle, endpoint_in, endpoint_out, &status);

        if (!running) {
            break;
        }
        if (result != 0) {
            fprintf(stderr, "L3210 button query failed: %s\n", libusb_error_name(result));
            libusb_release_interface(handle, interface_number);
            libusb_close(handle);
            handle = NULL;
            sleep(1);
            continue;
        }
        if (status != 0 && previous_status == 0) {
            fprintf(stderr, "L3210 button pressed: %u\n", status);
            int reset_result = initialize_scanner(handle, endpoint_in, endpoint_out);
            fprintf(stderr, "L3210 button handoff reset: %s\n", libusb_error_name(reset_result));
            libusb_release_interface(handle, interface_number);
            libusb_close(handle);
            handle = NULL;
            fprintf(stderr, "L3210 panel event released; waiting for native scan handoff\n");
            sleep(5);
            run_action(argv[1], status);
            previous_status = 0;
            needs_initialize = 1;
            sleep(2);
            continue;
        }
        previous_status = status;
        usleep(500000);
    }

    if (handle != NULL) {
        libusb_release_interface(handle, interface_number);
        libusb_close(handle);
    }
    libusb_exit(context);
    return 0;
}
