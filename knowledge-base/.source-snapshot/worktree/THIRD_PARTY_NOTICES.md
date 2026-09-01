# Third-party notices

The lite distribution vendors the pure-Python NetworkX 3.5 package and Graphify's unmodified community detector; their licenses, notices, wheel/source hashes, and provenance records are included under `scripts/_vendor/`. The full Windows x64 distribution additionally aggregates separate unmodified or reproducibly built tools listed in `toolchain.lock.json`.

- CPython: PSF License Version 2.
- Tree-sitter and the included grammar bindings: MIT licenses from their respective distributions.
- tree-sitter-c-sharp 0.23.5: MIT license and corresponding source archive.
- Node.js: MIT license and the third-party notices shipped by Node.js.
- Pyright and TypeScript Language Server: MIT licenses.
- TypeScript: Apache License 2.0.
- LLVM/clangd: Apache License 2.0 with LLVM Exceptions and bundled third-party notices.
- .NET SDK 10.0.400/runtime 10.0.11: MIT license and Microsoft third-party notices.
- csharp-ls 0.26.0: MIT license; the exact NuGet package and tagged source archive are included.
- Logseq CLI: GNU Affero General Public License version 3. The full distribution includes the exact corresponding source archive for commit `fab27740975dcda1e93dbca718d1f620eda543c7`; the CLI remains a separate process and is not linked into this Skill.
- Logseq default file-graph `config.edn`: an unmodified template from commit `fab27740975dcda1e93dbca718d1f620eda543c7`, included under the same GNU Affero General Public License version 3 terms and source provenance.
- Graphify community detector: unmodified `graphify/cluster.py` from Graphify `0.9.48`, commit `b2cd36267456c166788c95be6e68574064a92a42`; Apache License 2.0. The upstream `LICENSE`, `LICENSE-MIT`, and `NOTICE` are retained beside the source.
- NetworkX 3.5: unmodified pure-Python wheel content, BSD-3-Clause. Wheel metadata and license files are retained beside the package.

The full package preserves the license and notice files supplied by every component under `assets/runtime/win-x64/licenses/`.
