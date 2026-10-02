# CUPS Local Overlay

The upstream CUPS source is pinned as a read-only submodule. Preparation
archives that commit, applies the parent patch, and copies this overlay into a
disposable build tree. No upstream files are edited and re-running preparation
starts fresh.

The proxy on Supervisor bridge port 8098 rewrites CUPS HTML links and redirects
for ingress; CUPS IPP and AirPrint remain on port 631. The proxy connects from
the bridge address so it does not inherit the queue monitor's localhost
authorization exemption. CUPS administrative authentication remains enabled
for remote requests.

The existing native driver in `/config/e202101w` must be migrated alongside
`/config/cups`. Do not commit configuration, credentials, native libraries,
printer jobs, or scans. Upstream attribution remains in its submodule.
