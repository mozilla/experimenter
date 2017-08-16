printf '{"commit":"%s","version":"%s","source":"%s","build":"%s"}\n' \
  "$(git rev-parse HEAD)" \
  "$(git describe --tags)" \
  "$(git config --local remote.origin.url | sed -e s,git@github.com:,https://github.com/,)" \
  "$CIRCLE_BUILD_URL"
