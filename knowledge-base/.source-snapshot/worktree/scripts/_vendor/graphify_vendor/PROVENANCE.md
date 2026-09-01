# Graphify vendored component

- Upstream: `https://github.com/Graphify-Labs/graphify`
- Branch at acquisition: `v8`
- Commit: `b2cd36267456c166788c95be6e68574064a92a42`
- Upstream package version: `0.9.48`
- Included source: `graphify/cluster.py`
- Local path: `scripts/_vendor/graphify_vendor/cluster.py`
- License: Apache-2.0; historical MIT text and upstream NOTICE are retained.

The clustering source is copied without functional changes. The surrounding
`ckb_core.graphify_core` adapter is original integration code: it converts the
source-audited CKB canonical graph to Graphify's node-link confidence and
community model while retaining Git commit, blob, range, scope, and Agent-review
evidence that the CKB completion contract requires.
