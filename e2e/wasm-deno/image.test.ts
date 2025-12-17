// Auto-generated tests for image fixtures.
// Run with: deno test --allow-read

// @deno-types="../../crates/kreuzberg-wasm/dist/index.d.mts"
import { extractBytes } from "npm:@kreuzberg/wasm@^4.0.0";
import { assertions, buildConfig, resolveDocument, shouldSkipFixture } from "./helpers.ts";
// @deno-types="../../crates/kreuzberg-wasm/dist/index.d.mts"
import type { ExtractionResult } from "npm:@kreuzberg/wasm@^4.0.0";

Deno.test("image_metadata_only", { permissions: { read: true } }, async () => {
	const documentBytes = await resolveDocument("images/example.jpg");
	const config = buildConfig({ ocr: null });
	let result: ExtractionResult | null = null;
	try {
		result = await extractBytes(documentBytes, "application/pdf", config);
	} catch (error) {
		if (shouldSkipFixture(error, "image_metadata_only", [], undefined)) {
			return;
		}
		throw error;
	}
	if (result === null) {
		return;
	}
	assertions.assertExpectedMime(result, ["image/jpeg"]);
	assertions.assertMaxContentLength(result, 100);
});
