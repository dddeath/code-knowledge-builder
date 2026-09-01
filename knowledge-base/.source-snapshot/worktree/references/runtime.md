# Runtime and distribution

## Lite

The lite distribution contains no third-party runtime. `doctor` searches explicit environment overrides, the private runtime cache, and then `PATH`. It reports every missing tool and the expected version.

## Full Windows x64

The full distribution contains a locked offline payload. Detection still prefers a compatible host tool. When components are missing, `doctor` prints the component list, versions, payload size, private destination, and removal command, then exits `3`.

After the user explicitly approves the deployment:

```powershell
& PYTHON scripts\ckb.py runtime deploy --accept
```

The payload is extracted under `%USERPROFILE%\.codex\cache\code-knowledge-builder\runtime\win-x64\LOCK_ID`. System PATH, global npm/pip tools, global dotnet tools, and the global NuGet cache remain unchanged.

Remove the deployed payload with:

```powershell
& PYTHON scripts\ckb.py runtime remove --lock-id LOCK_ID
```

The runtime lock records exact versions, source URLs, archive hashes, included files, and licenses. Version 2 includes .NET SDK 10.0.400/runtime 10.0.11, csharp-ls 0.26.0, and tree-sitter-c-sharp 0.23.5. Their source archives/packages, build record, official .NET release SHA-512 verification, and licenses travel with the full distribution. Logseq remains a separate process and its corresponding AGPL source archive also travels with the full distribution.
