// Auto-generated tests for email fixtures.
// Run with: deno test --allow-read

// @deno-types="../../crates/kreuzberg-wasm/dist/index.d.mts"
import { extractBytes } from "npm:@kreuzberg/wasm@^4.0.0";
import { assertions, buildConfig, resolveDocument, shouldSkipFixture } from "./helpers.ts";
// @deno-types="../../crates/kreuzberg-wasm/dist/index.d.mts"
import type { ExtractionResult } from "npm:@kreuzberg/wasm@^4.0.0";

Deno.test("email_sample_eml", { permissions: { read: true } }, async () => {
	const documentBytes = await resolveDocument("email/sample_email.eml");
	const config = buildConfig(undefined);
	let result: ExtractionResult | null = null;
	try {
		result = await extractBytes(documentBytes, "application/pdf", config);
	} catch (error) {
		if (shouldSkipFixture(error, "email_sample_eml", [], undefined)) {
			return;
		}
		throw error;
	}
	if (result === null) {
		return;
	}
	assertions.assertExpectedMime(result, ["message/rfc822"]);
	assertions.assertMinContentLength(result, 20);
});
