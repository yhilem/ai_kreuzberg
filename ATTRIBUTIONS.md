# Third-Party Attributions

This file contains attributions for third-party code, data, and libraries used in Kreuzberg.

## Stopwords Data

The stopwords data in `kreuzberg/_token_reduction/stop_words.json` is derived from the [stopwords-iso](https://github.com/stopwords-iso/stopwords-iso) project.

**Original Author:** Gene Diaz and contributors
**License:** MIT License
**Source:** <https://github.com/stopwords-iso/stopwords-iso>

### MIT License (stopwords-iso)

```text
MIT License

Copyright (c) stopwords-iso contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Changes Made

The original stopwords-iso data was used as-is with no modifications to the word lists themselves. The data was packaged into Kreuzberg's `_token_reduction` module for use in the token reduction feature.

______________________________________________________________________

## Other Third-Party Dependencies

All other third-party dependencies are listed in `pyproject.toml` with their respective licenses. This section is specifically for bundled/vendored code and data.
