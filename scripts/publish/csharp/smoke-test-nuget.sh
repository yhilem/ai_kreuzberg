#!/usr/bin/env bash

set -euo pipefail

version="${VERSION:?VERSION not set}"
pkg_dir="$(pwd)/dist"

if command -v cygpath >/dev/null 2>&1; then
	pkg_dir="$(cygpath -w "$pkg_dir")"
fi

tmp="$(mktemp -d)"
dotnet new console -n KreuzbergSmoke -o "$tmp/KreuzbergSmoke"

# Copy test document to temp directory
mkdir -p "$tmp/test_documents/pdf"
cp "test_documents/pdf/simple.pdf" "$tmp/test_documents/pdf/"

cat >"$tmp/KreuzbergSmoke/KreuzbergSmoke.csproj" <<EOF
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Kreuzberg" Version="$version" />
  </ItemGroup>
</Project>
EOF

cat >"$tmp/KreuzbergSmoke/Program.cs" <<'EOF'
using Kreuzberg;
using System;
using System.IO;

var pdfPath = Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "test_documents", "pdf", "simple.pdf"));
if (!File.Exists(pdfPath))
{
    throw new FileNotFoundException($"Missing test document: {pdfPath}");
}

var result = KreuzbergClient.ExtractFileSync(pdfPath);
Console.WriteLine($"mime={result.MimeType} len={result.Content.Length}");
EOF

dotnet restore "$tmp/KreuzbergSmoke" --source "$pkg_dir" --source "https://api.nuget.org/v3/index.json"
cd "$tmp"
dotnet run --project "$tmp/KreuzbergSmoke" -c Release
