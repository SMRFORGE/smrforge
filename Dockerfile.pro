# SMRForge Pro Dockerfile — See smrforge-pro repo
#
# Pro tier lives in https://github.com/SMRFORGE/smrforge-pro (private).
# Pro adds: Serpent/MCNP full export+import, CAD/DAGMC import, advanced variance reduction (CADIS),
# OpenMC tally viz, AI/surrogate, regulatory package. Air-gap Pro = full Pro (feature parity).
# This Community repo has no smrforge_pro/ — placeholder only.
#
# To build Pro:
#   Clone smrforge-pro, then: docker build -f Dockerfile.pro -t smrforge-pro:latest .
#
# Community images: docker build -t smrforge:latest . (uses Dockerfile)

FROM python:3.11-slim
LABEL org.opencontainers.image.title="SMRForge Pro Placeholder" \
      org.opencontainers.image.description="Pro builds in smrforge-pro repo"
RUN echo "ERROR: Pro Dockerfile must be built from smrforge-pro repo. See https://github.com/SMRFORGE/smrforge-pro" && exit 1
