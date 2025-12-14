#!/usr/bin/env bash
set -euo pipefail

jar_dir="${1:-artifacts/java}"
jar=""

for f in "$jar_dir"/kreuzberg-*.jar; do
	case "$f" in
	*-sources.jar | *-javadoc.jar) continue ;;
	esac
	jar="$f"
	break
done

if [ -z "$jar" ] || [ ! -f "$jar" ]; then
	echo "No kreuzberg jar found in $jar_dir" >&2
	ls -la "$jar_dir" >&2 || true
	exit 1
fi

tmp="$(mktemp -d)"
cat >"$tmp/Smoke.java" <<'EOF'
import dev.kreuzberg.Kreuzberg;

public class Smoke {
    public static void main(String[] args) {
        System.out.println(Kreuzberg.getVersion());
    }
}
EOF

sep=":"
jar_cp="$jar"
tmp_cp="$tmp"
src_cp="$tmp/Smoke.java"

if [ "${RUNNER_OS:-}" = "Windows" ]; then
	sep=";"
	if command -v cygpath >/dev/null 2>&1; then
		jar_cp="$(cygpath -w "$jar")"
		tmp_cp="$(cygpath -w "$tmp")"
		src_cp="$(cygpath -w "$tmp/Smoke.java")"
	fi
fi

javac --release 25 -cp "$jar_cp" "$src_cp"

java --enable-native-access=ALL-UNNAMED -cp "$jar_cp$sep$tmp_cp" Smoke
