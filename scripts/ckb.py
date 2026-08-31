#!/usr/bin/env python3
"""Build and audit a segmented code navigation knowledge base."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Running the CLI from a clean source repository must not create __pycache__
# before Git preflight inspects that repository.  Full/lite launchers can still
# opt into a separate bytecode cache through their host environment if needed.
sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ckb_core.common import CkbError, DependencyError, ReviewRequired
from ckb_core.agent_index import build_agent_index, retrieve
from ckb_core.agent_maintenance import finish_session, sessions_status, start_session
from ckb_core.agent_protocol import (
    agent_protocol_status,
    audit_agent_protocol,
    install_agent_protocol,
)
from ckb_core.automation import (
    SUPPORTED_HARNESSES,
    activate_skill_session,
    automation_status,
    default_registry_path,
    drain_automation,
    ingest_event,
    pending_automation_reviews,
    register_project,
    registry_status,
    retry_failed_automation,
    review_automation,
    unregister_project,
    write_automation_review_template,
)
from ckb_core.automation_integrations import render_integration
from ckb_core.gitrepo import DEFAULT_INITIAL_COMMIT_MESSAGE
from ckb_core.feedback import (
    audit_feedback,
    create_feedback,
    list_feedback,
    locate_feedback,
    resolve_feedback,
)
from ckb_core.graphify_core import explain_node, query_graph, shortest_path
from ckb_core.machine_knowledge import (
    build_machine_knowledge,
    change_documents,
    coverage as machine_coverage,
    entity_lookup,
    neighbor_lookup,
    retrieve_machine,
    source_lookup,
    sync_workspace_changes,
)
from ckb_core.llm_wiki_capabilities import (
    capability_matrix,
    compact_agent_brief,
    maintenance_check,
    render_capability_matrix_markdown,
    write_capability_matrix,
)
from ckb_core.keyword_fallback import (
    KeywordFallbackOptions,
    KeywordProviderConfig,
    validate_provider_config,
)
from ckb_core.migration import audit_migration, migrate_output, migration_status
from ckb_core.page_config import (
    DEFAULT_PAGE_CONFIG,
    load_page_config,
    page_config_sha256,
    write_page_config,
)
from ckb_core.pipeline import (
    audit_chunk,
    audit_global,
    build_chunk,
    build_context,
    finalize,
    initialize,
    merge,
    relink_sources,
    refresh_human_navigation,
    review_chunk,
    review_pack,
    run_fast,
    status,
)
from ckb_core.providers import doctor_report
from ckb_core.runtime import deploy as deploy_runtime
from ckb_core.runtime import deployment_plan, remove as remove_runtime
from ckb_core.reference_documents import (
    audit_references,
    ingest_reference,
    list_references,
    rollback_reference,
    submit_reference_review,
    write_reference_review_template,
)
from ckb_core.research_gaps import (
    GAP_KINDS,
    GAP_STATUSES,
    audit_gap_register,
    create_gap,
    list_gaps,
    resolve_gap,
)
from ckb_core.obsidian_plugin import (
    deploy_obsidian_plugin,
    obsidian_plugin_status,
    register_obsidian_plugin,
    remove_obsidian_plugin,
)
from ckb_core.operation_journal import (
    OPERATION_TYPES,
    audit_operation_journal,
    list_operations,
    record_cli_operation,
)
from ckb_core.showcase import package_showcase
from ckb_core.stdio_server import serve_stdio
from ckb_core.workspace_notes import record_note, sync_workspace, workspace_status


def add_initial_arguments(parser: argparse.ArgumentParser, required: bool = True) -> None:
    parser.add_argument("--repo", type=Path, required=required)
    parser.add_argument("--out", type=Path, required=required)
    parser.add_argument("--format", choices=("markdown", "logseq-db", "both"), required=required)
    parser.add_argument("--scope-path", action="append", default=[])
    parser.add_argument("--entry", action="append", default=[])
    parser.add_argument("--expand-depth", type=int, default=1)
    parser.add_argument("--expand-direction", choices=("both", "callers", "callees"), default="both")
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument(
        "--page-config",
        type=Path,
        help="partial or complete JSON page configuration; normalized bytes are pinned into OUTPUT/page-config.json",
    )
    add_csharp_arguments(parser)
    add_git_bootstrap_arguments(parser)


def add_csharp_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--csharp-solution")
    parser.add_argument("--csharp-project")
    parser.add_argument("--allow-dotnet-restore", action="store_true")


def add_git_bootstrap_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--init-git",
        action="store_true",
        help="if the path has no commit, initialize Git, stage current files, and create exactly one initial commit",
    )
    parser.add_argument("--initial-commit-message", default=DEFAULT_INITIAL_COMMIT_MESSAGE)
    parser.add_argument("--git-author-name")
    parser.add_argument("--git-author-email")


def add_keyword_fallback_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument("--allow-keyword-fallback", action="store_true")
    command.add_argument("--force-keyword-fallback", action="store_true")
    command.add_argument("--keyword-provider-command")
    command.add_argument("--keyword-provider-arg", action="append", default=[])
    command.add_argument("--keyword-provider", dest="keyword_provider_name")
    command.add_argument("--keyword-model")
    command.add_argument("--keyword-provider-version")
    command.add_argument("--keyword-provider-timeout", type=float, default=20.0)
    command.add_argument("--keyword-provider-retries", type=int, choices=(0, 1), default=1)
    command.add_argument("--keyword-provider-require-env", action="append", default=[])
    command.add_argument("--keyword-provider-no-cache", action="store_true")


def keyword_fallback_options(args: argparse.Namespace) -> KeywordFallbackOptions | None:
    if not (args.allow_keyword_fallback or args.force_keyword_fallback):
        return None
    required = {
        "--keyword-provider-command": args.keyword_provider_command,
        "--keyword-provider": args.keyword_provider_name,
        "--keyword-model": args.keyword_model,
        "--keyword-provider-version": args.keyword_provider_version,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise CkbError("keyword fallback requires " + ", ".join(missing))
    config = KeywordProviderConfig(
        command=(args.keyword_provider_command, *args.keyword_provider_arg),
        provider=args.keyword_provider_name,
        model=args.keyword_model,
        version=args.keyword_provider_version,
        timeout_seconds=args.keyword_provider_timeout,
        retries=args.keyword_provider_retries,
        required_environment=tuple(args.keyword_provider_require_env),
    )
    validate_provider_config(config)
    return KeywordFallbackOptions(
        config=config,
        force=bool(args.force_keyword_fallback),
        use_cache=not args.keyword_provider_no_cache,
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--json", action="store_true")
    init = sub.add_parser("init")
    add_initial_arguments(init)
    fast = sub.add_parser("run")
    fast.add_argument("--repo", type=Path)
    fast.add_argument("--out", type=Path, required=True)
    fast.add_argument("--format", choices=("markdown", "logseq-db", "both"))
    fast.add_argument("--scope-path", action="append", default=[])
    fast.add_argument("--entry", action="append", default=[])
    fast.add_argument("--expand-depth", type=int, default=1)
    fast.add_argument("--expand-direction", choices=("both", "callers", "callees"), default="both")
    fast.add_argument("--include", action="append", default=[])
    fast.add_argument("--page-config", type=Path)
    add_csharp_arguments(fast)
    add_git_bootstrap_arguments(fast)
    fast.add_argument("--resume", action="store_true")
    build = sub.add_parser("build-chunk")
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--chunk", required=True)
    build.add_argument("--stage", choices=("syntax", "semantics", "classify", "project", "all"), default="all")
    review = sub.add_parser("review-chunk")
    review.add_argument("--out", type=Path, required=True)
    review.add_argument("--chunk", required=True)
    review.add_argument("--review", type=Path, required=True)
    review_pack_command = sub.add_parser("review-pack")
    review_pack_command.add_argument("--out", type=Path, required=True)
    review_pack_command.add_argument("--pack", required=True)
    review_pack_command.add_argument("--review", type=Path, required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("--out", type=Path, required=True)
    group = audit.add_mutually_exclusive_group(required=True)
    group.add_argument("--chunk")
    group.add_argument("--global", dest="global_audit", action="store_true")
    merge_command = sub.add_parser("merge")
    merge_command.add_argument("--out", type=Path, required=True)
    final = sub.add_parser("finalize")
    final.add_argument("--out", type=Path, required=True)
    status_command = sub.add_parser("status")
    status_command.add_argument("--out", type=Path, required=True)
    status_command.add_argument("--json", action="store_true")
    human_refresh_command = sub.add_parser("human-refresh")
    human_refresh_command.add_argument("--out", type=Path, required=True)
    human_refresh_command.add_argument("--staging", action="store_true")
    migration_command = sub.add_parser("migrate")
    migration_sub = migration_command.add_subparsers(dest="migration_command", required=True)
    migration_start = migration_sub.add_parser("start")
    migration_start.add_argument("--from-out", type=Path, required=True)
    migration_start.add_argument("--repo", type=Path, required=True)
    migration_start.add_argument("--out", type=Path, required=True)
    migration_start.add_argument("--format", choices=("markdown", "logseq-db", "both"))
    migration_status_command = migration_sub.add_parser("status")
    migration_status_command.add_argument("--out", type=Path, required=True)
    migration_audit_command = migration_sub.add_parser("audit")
    migration_audit_command.add_argument("--out", type=Path, required=True)
    migration_audit_command.add_argument("--allow-pending-reviews", action="store_true")
    context_command = sub.add_parser("context")
    context_command.add_argument("--out", type=Path, required=True)
    context_command.add_argument("--module", required=True)
    context_command.add_argument("--entry")
    query_command = sub.add_parser("query")
    query_command.add_argument("--out", type=Path, required=True)
    query_command.add_argument("question")
    query_command.add_argument("--budget", type=int, default=1500)
    query_command.add_argument("--dfs", action="store_true")
    retrieve_command = sub.add_parser("retrieve")
    retrieve_command.add_argument("--out", type=Path, required=True)
    retrieve_command.add_argument("question")
    retrieve_command.add_argument("--budget", type=int, default=1500)
    retrieve_command.add_argument("--max-pages", type=int, default=8)
    retrieve_command.add_argument("--profile", choices=("fast", "precise"), default="fast")
    add_keyword_fallback_arguments(retrieve_command)
    brief_command = sub.add_parser("brief")
    brief_command.add_argument("--out", type=Path, required=True)
    brief_command.add_argument("question")
    brief_command.add_argument("--budget", type=int, default=1800)
    brief_command.add_argument("--max-pages", type=int, default=8)
    brief_command.add_argument("--profile", choices=("fast", "precise"), default="fast")
    add_keyword_fallback_arguments(brief_command)
    capabilities_command = sub.add_parser("capabilities")
    capabilities_command.add_argument("--format", choices=("json", "markdown"), default="json")
    capabilities_command.add_argument("--write", type=Path)
    maintain_command = sub.add_parser("maintain")
    maintain_command.add_argument("--out", type=Path, required=True)
    operations_command = sub.add_parser("operations")
    operations_sub = operations_command.add_subparsers(dest="operations_command", required=True)
    operations_list = operations_sub.add_parser("list")
    operations_list.add_argument("--out", type=Path, required=True)
    operations_list.add_argument("--operation", choices=OPERATION_TYPES)
    operations_list.add_argument("--status", dest="result_status")
    operations_list.add_argument("--limit", type=int, default=50)
    operations_audit = operations_sub.add_parser("audit")
    operations_audit.add_argument("--out", type=Path, required=True)
    gaps_command = sub.add_parser("gaps")
    gaps_sub = gaps_command.add_subparsers(dest="gaps_command", required=True)
    gaps_create = gaps_sub.add_parser("create")
    gaps_create.add_argument("--out", type=Path, required=True)
    gaps_create.add_argument("--kind", choices=GAP_KINDS, required=True)
    gaps_create.add_argument("--summary", type=Path, required=True)
    gaps_create.add_argument("--evidence", action="append", required=True)
    gaps_list = gaps_sub.add_parser("list")
    gaps_list.add_argument("--out", type=Path, required=True)
    gaps_list.add_argument("--status", choices=GAP_STATUSES)
    gaps_list.add_argument("--kind", choices=GAP_KINDS)
    gaps_resolve = gaps_sub.add_parser("resolve")
    gaps_resolve.add_argument("--out", type=Path, required=True)
    gaps_resolve.add_argument("--gap", required=True)
    gaps_resolve.add_argument("--resolution", type=Path, required=True)
    gaps_resolve.add_argument("--evidence", action="append", required=True)
    gaps_audit = gaps_sub.add_parser("audit")
    gaps_audit.add_argument("--out", type=Path, required=True)
    reference_command = sub.add_parser("reference")
    reference_sub = reference_command.add_subparsers(dest="reference_command", required=True)
    reference_ingest = reference_sub.add_parser("ingest")
    reference_ingest.add_argument("--out", type=Path, required=True)
    reference_ingest.add_argument("--source", type=Path, required=True)
    reference_ingest.add_argument("--title", required=True)
    reference_ingest.add_argument("--origin", required=True)
    reference_ingest.add_argument("--license", dest="license_name", required=True)
    reference_ingest.add_argument("--author")
    reference_ingest.add_argument("--revision-of")
    reference_template = reference_sub.add_parser("review-template")
    reference_template.add_argument("--out", type=Path, required=True)
    reference_template.add_argument("--reference", required=True)
    reference_template.add_argument("--write", type=Path, required=True)
    reference_review = reference_sub.add_parser("review")
    reference_review.add_argument("--out", type=Path, required=True)
    reference_review.add_argument("--review", type=Path, required=True)
    reference_audit = reference_sub.add_parser("audit")
    reference_audit.add_argument("--out", type=Path, required=True)
    reference_list = reference_sub.add_parser("list")
    reference_list.add_argument("--out", type=Path, required=True)
    reference_list.add_argument("--status", choices=("all", "pending-agent-review", "agent-reviewed", "superseded"), default="all")
    reference_rollback = reference_sub.add_parser("rollback")
    reference_rollback.add_argument("--out", type=Path, required=True)
    reference_rollback.add_argument("--reference", required=True)
    serve_command = sub.add_parser("serve")
    serve_command.add_argument("--out", type=Path, required=True)
    serve_command.add_argument("--stdio", action="store_true", required=True)
    reindex_command = sub.add_parser("reindex")
    reindex_command.add_argument("--out", type=Path, required=True)
    coverage_command = sub.add_parser("coverage")
    coverage_command.add_argument("--out", type=Path, required=True)
    entity_command = sub.add_parser("entity")
    entity_command.add_argument("--out", type=Path, required=True)
    entity_command.add_argument("selector")
    neighbors_command = sub.add_parser("neighbors")
    neighbors_command.add_argument("--out", type=Path, required=True)
    neighbors_command.add_argument("selector")
    neighbors_command.add_argument("--depth", type=int, default=1)
    neighbors_command.add_argument("--relation")
    neighbors_command.add_argument("--limit", type=int, default=50)
    source_command = sub.add_parser("source")
    source_command.add_argument("--out", type=Path, required=True)
    source_command.add_argument("selector")
    source_command.add_argument("--context-lines", type=int, default=3)
    changes_command = sub.add_parser("changes")
    changes_command.add_argument("--out", type=Path, required=True)
    changes_command.add_argument("--kind", choices=("analysis", "change", "pitfall", "experiment", "session"))
    changes_command.add_argument("--limit", type=int, default=20)
    path_command = sub.add_parser("path")
    path_command.add_argument("--out", type=Path, required=True)
    path_command.add_argument("source")
    path_command.add_argument("target")
    explain_command = sub.add_parser("explain")
    explain_command.add_argument("--out", type=Path, required=True)
    explain_command.add_argument("selector")
    record_command = sub.add_parser("record")
    record_command.add_argument("--out", type=Path, required=True)
    record_command.add_argument("--kind", choices=("analysis", "change", "pitfall", "experiment", "session"), required=True)
    record_command.add_argument("--title", required=True)
    record_command.add_argument("--body", type=Path, required=True)
    record_command.add_argument("--link", action="append", default=[])
    record_source = record_command.add_mutually_exclusive_group()
    record_source.add_argument("--from-query", type=Path)
    record_source.add_argument("--from-pack", type=Path)
    record_command.add_argument("--append", action="store_true")
    feedback_command = sub.add_parser("feedback")
    feedback_sub = feedback_command.add_subparsers(dest="feedback_command", required=True)
    feedback_create = feedback_sub.add_parser("create")
    feedback_create.add_argument("--out", type=Path, required=True)
    feedback_create.add_argument("--target", type=Path, required=True)
    feedback_create.add_argument("--start-line", type=int, required=True)
    feedback_create.add_argument("--end-line", type=int, required=True)
    feedback_create.add_argument("--comment", type=Path, required=True)
    feedback_create.add_argument("--severity", choices=("error", "warn", "suggest", "info"), default="suggest")
    feedback_create.add_argument("--author", required=True)
    feedback_create.add_argument("--source", choices=("manual", "obsidian-plugin", "web-viewer"), default="manual")
    feedback_list = feedback_sub.add_parser("list")
    feedback_list.add_argument("--out", type=Path, required=True)
    feedback_list.add_argument("--status", choices=("open", "resolved", "all"), default="open")
    feedback_locate = feedback_sub.add_parser("locate")
    feedback_locate.add_argument("--out", type=Path, required=True)
    feedback_locate.add_argument("--feedback", required=True)
    feedback_resolve = feedback_sub.add_parser("resolve")
    feedback_resolve.add_argument("--out", type=Path, required=True)
    feedback_resolve.add_argument("--feedback", required=True)
    feedback_resolve.add_argument("--decision", choices=("accepted", "partial", "rejected", "deferred"), required=True)
    feedback_resolve.add_argument("--resolution", type=Path, required=True)
    feedback_resolve.add_argument("--applied-record", type=Path)
    feedback_audit = feedback_sub.add_parser("audit")
    feedback_audit.add_argument("--out", type=Path, required=True)
    workspace_command = sub.add_parser("workspace")
    workspace_sub = workspace_command.add_subparsers(dest="workspace_command", required=True)
    workspace_sync_command = workspace_sub.add_parser("sync")
    workspace_sync_command.add_argument("--out", type=Path, required=True)
    workspace_sync_command.add_argument("--repo", type=Path, required=True)
    workspace_status_command = workspace_sub.add_parser("status")
    workspace_status_command.add_argument("--out", type=Path, required=True)
    workspace_start_command = workspace_sub.add_parser("session-start")
    workspace_start_command.add_argument("--out", type=Path, required=True)
    workspace_start_command.add_argument("--repo", type=Path, required=True)
    workspace_start_command.add_argument("--question", required=True)
    workspace_start_command.add_argument("--budget", type=int, default=1800)
    workspace_start_command.add_argument("--profile", choices=("fast", "precise"), default="fast")
    workspace_finish_command = workspace_sub.add_parser("session-finish")
    workspace_finish_command.add_argument("--out", type=Path, required=True)
    workspace_finish_command.add_argument("--repo", type=Path, required=True)
    workspace_finish_command.add_argument("--session", required=True)
    workspace_finish_command.add_argument("--summary", type=Path, required=True)
    workspace_finish_command.add_argument("--title")
    workspace_sessions_command = workspace_sub.add_parser("sessions")
    workspace_sessions_command.add_argument("--out", type=Path, required=True)
    agent_policy_command = sub.add_parser("agent-policy")
    agent_policy_sub = agent_policy_command.add_subparsers(dest="agent_policy_command", required=True)
    agent_policy_install = agent_policy_sub.add_parser("install")
    agent_policy_install.add_argument("--out", type=Path, required=True)
    agent_policy_install.add_argument("--workspace-root", type=Path, action="append", default=[])
    agent_policy_install.add_argument("--python", type=Path)
    agent_policy_install.add_argument("--ckb", type=Path)
    agent_policy_check = agent_policy_sub.add_parser("check")
    agent_policy_check.add_argument("--out", type=Path, required=True)
    agent_policy_status_command = agent_policy_sub.add_parser("status")
    agent_policy_status_command.add_argument("--out", type=Path, required=True)
    automation_command = sub.add_parser("automation")
    automation_sub = automation_command.add_subparsers(dest="automation_command", required=True)
    automation_register = automation_sub.add_parser("register")
    automation_register.add_argument("--repo", type=Path, required=True)
    automation_register.add_argument("--out", type=Path, required=True)
    automation_register.add_argument("--registry", type=Path, default=default_registry_path())
    automation_register.add_argument("--harness", action="append", choices=sorted(SUPPORTED_HARNESSES), default=[])
    automation_register.add_argument("--max-field-chars", type=int, default=12_000)
    automation_register.add_argument("--redact", action="append", default=[])
    automation_register.add_argument(
        "--workspace-root",
        type=Path,
        action="append",
        default=[],
        help="repeatable Harness task root that maps to --repo while keeping scratch files outside the Git boundary",
    )
    automation_unregister = automation_sub.add_parser("unregister")
    automation_unregister.add_argument("--repo", type=Path, required=True)
    automation_unregister.add_argument("--registry", type=Path, default=default_registry_path())
    automation_registry = automation_sub.add_parser("registry")
    automation_registry.add_argument("--registry", type=Path, default=default_registry_path())
    automation_activate = automation_sub.add_parser("activate")
    automation_activate.add_argument("--harness", choices=sorted(SUPPORTED_HARNESSES), required=True)
    automation_activate.add_argument("--session-id")
    automation_activate.add_argument("--cwd", type=Path, default=Path.cwd())
    automation_activate.add_argument("--registry", type=Path, default=default_registry_path())
    automation_activate.add_argument("--source", default="agent-skill-start")
    for name in ("ingest", "hook"):
        parser_value = automation_sub.add_parser(name)
        parser_value.add_argument("--harness", choices=sorted(SUPPORTED_HARNESSES), required=True)
        parser_value.add_argument("--registry", type=Path, default=default_registry_path())
        parser_value.add_argument("--event", type=Path, help="JSON event file; omit to read one JSON object from stdin")
    automation_drain = automation_sub.add_parser("drain")
    automation_drain.add_argument("--out", type=Path, required=True)
    automation_drain.add_argument("--limit", type=int, default=500)
    automation_retry = automation_sub.add_parser("retry")
    automation_retry.add_argument("--out", type=Path, required=True)
    automation_retry.add_argument("--limit", type=int, default=500)
    automation_status_command = automation_sub.add_parser("status")
    automation_status_command.add_argument("--out", type=Path, required=True)
    automation_pending = automation_sub.add_parser("pending")
    automation_pending.add_argument("--out", type=Path, required=True)
    automation_pending.add_argument("--all", action="store_true")
    automation_review = automation_sub.add_parser("review")
    automation_review.add_argument("--out", type=Path, required=True)
    automation_review.add_argument("--review", type=Path, required=True)
    automation_template = automation_sub.add_parser("review-template")
    automation_template.add_argument("--out", type=Path, required=True)
    automation_template.add_argument("--review-id", required=True)
    automation_template.add_argument("--write", type=Path, required=True)
    automation_render = automation_sub.add_parser("render")
    automation_render.add_argument("--harness", choices=sorted(SUPPORTED_HARNESSES), required=True)
    automation_render.add_argument("--destination", type=Path, required=True)
    automation_render.add_argument("--python", type=Path)
    automation_render.add_argument("--ckb", type=Path)
    automation_render.add_argument("--registry", type=Path, default=default_registry_path())
    automation_render.add_argument("--force", action="store_true")
    relink_command = sub.add_parser("relink")
    relink_command.add_argument("--out", type=Path, required=True)
    relink_command.add_argument("--repo-root", type=Path, required=True)
    relink_command.add_argument("--editor", choices=("vscode", "vscode-insiders", "file", "custom-template"), default="vscode")
    relink_command.add_argument("--source-view", choices=("working", "baseline"), default="working")
    relink_command.add_argument("--custom-template")
    showcase_command = sub.add_parser("showcase")
    showcase_command.add_argument("--dist", type=Path, required=True)
    showcase_command.add_argument("--sample", action="append", default=[], help="repeat LABEL=OUTPUT for each completed sample")
    page_config_command = sub.add_parser("page-config")
    page_config_group = page_config_command.add_mutually_exclusive_group(required=True)
    page_config_group.add_argument("--write", type=Path, help="write the complete built-in default JSON")
    page_config_group.add_argument("--validate", type=Path, help="validate and normalize a partial or complete JSON")
    page_config_command.add_argument("--force", action="store_true", help="replace an existing --write target")
    runtime = sub.add_parser("runtime")
    runtime_sub = runtime.add_subparsers(dest="runtime_command", required=True)
    runtime_plan = runtime_sub.add_parser("plan")
    runtime_plan.add_argument("--json", action="store_true")
    runtime_deploy = runtime_sub.add_parser("deploy")
    runtime_deploy.add_argument("--accept", action="store_true")
    runtime_remove = runtime_sub.add_parser("remove")
    runtime_remove.add_argument("--lock-id", required=True)
    obsidian_plugin_command = sub.add_parser("obsidian-plugin")
    obsidian_plugin_sub = obsidian_plugin_command.add_subparsers(dest="obsidian_plugin_command", required=True)
    obsidian_plugin_register = obsidian_plugin_sub.add_parser("register")
    obsidian_plugin_register.add_argument("--package", type=Path, required=True)
    obsidian_plugin_deploy = obsidian_plugin_sub.add_parser("deploy")
    obsidian_plugin_deploy.add_argument("--out", type=Path, required=True)
    obsidian_plugin_status_command = obsidian_plugin_sub.add_parser("status")
    obsidian_plugin_status_command.add_argument("--out", type=Path)
    obsidian_plugin_remove = obsidian_plugin_sub.add_parser("remove")
    obsidian_plugin_remove.add_argument("--out", type=Path, required=True)
    return root


_ACTIVE_ARGS: argparse.Namespace | None = None


def emit(value) -> None:
    if _ACTIVE_ARGS is not None:
        record_cli_operation(_ACTIVE_ARGS, value)
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    global _ACTIVE_ARGS
    args = parser().parse_args()
    _ACTIVE_ARGS = args
    if args.command == "doctor":
        report = doctor_report()
        report["runtime"] = deployment_plan()
        emit(report)
        return 0 if report["status"] == "ready" else 3
    if args.command == "init":
        emit(initialize(args.repo.resolve(), args.out.resolve(), args.format, args.scope_path, args.entry, args.expand_depth, args.expand_direction, args.include, args.init_git, args.initial_commit_message, args.git_author_name, args.git_author_email, args.csharp_solution, args.csharp_project, args.allow_dotnet_restore, args.page_config.resolve() if args.page_config else None))
    elif args.command == "run":
        emit(run_fast(repo=args.repo.resolve() if args.repo else None, output=args.out.resolve(), format_name=args.format, resume=args.resume, scope_paths=args.scope_path, entries=args.entry, expand_depth=args.expand_depth, expand_direction=args.expand_direction, includes=args.include, init_git=args.init_git, initial_commit_message=args.initial_commit_message, git_author_name=args.git_author_name, git_author_email=args.git_author_email, csharp_solution=args.csharp_solution, csharp_project=args.csharp_project, allow_dotnet_restore=args.allow_dotnet_restore, page_config_path=args.page_config.resolve() if args.page_config else None))
    elif args.command == "build-chunk":
        emit(build_chunk(args.out.resolve(), args.chunk, args.stage))
    elif args.command == "review-chunk":
        emit(review_chunk(args.out.resolve(), args.chunk, args.review.resolve()))
    elif args.command == "review-pack":
        emit(review_pack(args.out.resolve(), args.pack, args.review.resolve()))
    elif args.command == "audit":
        result = audit_global(args.out.resolve()) if args.global_audit else audit_chunk(args.out.resolve(), args.chunk)
        emit(result)
        return 0 if result.get("status") == "passed" else 5
    elif args.command == "merge":
        emit(merge(args.out.resolve()))
    elif args.command == "finalize":
        emit(finalize(args.out.resolve()))
    elif args.command == "status":
        emit(status(args.out.resolve()))
    elif args.command == "human-refresh":
        result = refresh_human_navigation(args.out.resolve(), staging=args.staging)
        emit(result)
        return 0 if result.get("status") == "passed" else 5
    elif args.command == "migrate":
        if args.migration_command == "start":
            result = migrate_output(args.from_out, args.repo, args.out, args.format)
            emit(result)
            return 4 if result.get("status") == "pending-agent-review" else 0
        if args.migration_command == "status":
            result = migration_status(args.out)
            emit(result)
            return 4 if result.get("status") == "pending-agent-review" else 0
        result = audit_migration(args.out, require_complete_reviews=not args.allow_pending_reviews)
        emit(result)
        return 0 if result.get("status") == "passed" else 4 if result.get("status") == "pending-agent-review" else 5
    elif args.command == "context":
        emit(build_context(args.out.resolve(), args.module, args.entry))
    elif args.command == "query":
        emit(query_graph(args.out.resolve(), args.question, args.budget, args.dfs))
    elif args.command == "retrieve":
        output = args.out.resolve()
        if (output / "machine/knowledge.sqlite").is_file():
            emit(
                retrieve_machine(
                    output,
                    args.question,
                    args.budget,
                    args.max_pages,
                    args.profile,
                    keyword_fallback=keyword_fallback_options(args),
                )
            )
        else:
            emit(retrieve(output, args.question, args.budget, args.max_pages))
    elif args.command == "brief":
        output = args.out.resolve()
        retrieval_result = (
            retrieve_machine(
                output,
                args.question,
                args.budget,
                args.max_pages,
                args.profile,
                keyword_fallback=keyword_fallback_options(args),
            )
            if (output / "machine/knowledge.sqlite").is_file()
            else retrieve(output, args.question, args.budget, args.max_pages)
        )
        emit(compact_agent_brief(output, retrieval_result))
    elif args.command == "capabilities":
        if args.write:
            emit(write_capability_matrix(args.write, args.format))
        elif args.format == "markdown":
            print(render_capability_matrix_markdown(), end="")
        else:
            emit(capability_matrix())
    elif args.command == "maintain":
        result = maintenance_check(args.out.resolve())
        emit(result)
        return 0 if result.get("status") == "passed" else 5
    elif args.command == "operations":
        if args.operations_command == "list":
            emit(list_operations(args.out.resolve(), args.operation, args.result_status, args.limit))
        else:
            result = audit_operation_journal(args.out.resolve())
            emit(result)
            return 0 if result.get("status") == "passed" else 5
    elif args.command == "gaps":
        if args.gaps_command == "create":
            emit(create_gap(args.out.resolve(), args.kind, args.summary.resolve(), args.evidence))
        elif args.gaps_command == "list":
            emit(list_gaps(args.out.resolve(), args.status, args.kind))
        elif args.gaps_command == "resolve":
            emit(resolve_gap(args.out.resolve(), args.gap, args.resolution.resolve(), args.evidence))
        else:
            result = audit_gap_register(args.out.resolve())
            emit(result)
            return 0 if result.get("status") == "passed" else 5
    elif args.command == "reference":
        if args.reference_command == "ingest":
            result = ingest_reference(
                args.out.resolve(), args.source.resolve(), args.title, args.origin, args.license_name,
                args.author, args.revision_of,
            )
            emit(result)
            return 4 if result.get("status") == "pending-agent-review" else 0
        if args.reference_command == "review-template":
            emit(write_reference_review_template(args.out.resolve(), args.reference, args.write))
        elif args.reference_command == "review":
            emit(submit_reference_review(args.out.resolve(), args.review.resolve()))
        elif args.reference_command == "audit":
            result = audit_references(args.out.resolve())
            emit(result)
            return 0 if result.get("status") == "passed" else 4 if result.get("status") == "pending-agent-review" else 5
        elif args.reference_command == "list":
            emit(list_references(args.out.resolve(), args.status))
        else:
            emit(rollback_reference(args.out.resolve(), args.reference))
    elif args.command == "serve":
        serve_stdio(args.out.resolve())
    elif args.command == "reindex":
        output = args.out.resolve()
        emit({"status": "passed", "machine": build_machine_knowledge(output), "compatibility": build_agent_index(output)})
    elif args.command == "coverage":
        emit(machine_coverage(args.out.resolve()))
    elif args.command == "entity":
        emit(entity_lookup(args.out.resolve(), args.selector))
    elif args.command == "neighbors":
        emit(neighbor_lookup(args.out.resolve(), args.selector, args.depth, args.relation, args.limit))
    elif args.command == "source":
        emit(source_lookup(args.out.resolve(), args.selector, args.context_lines))
    elif args.command == "changes":
        emit(change_documents(args.out.resolve(), args.kind, args.limit))
    elif args.command == "path":
        emit(shortest_path(args.out.resolve(), args.source, args.target))
    elif args.command == "explain":
        emit(explain_node(args.out.resolve(), args.selector))
    elif args.command == "record":
        emit(
            record_note(
                args.out.resolve(),
                args.kind,
                args.title,
                args.body.resolve(),
                args.link,
                (args.from_query or args.from_pack).resolve() if (args.from_query or args.from_pack) else None,
                args.append,
            )
        )
    elif args.command == "obsidian-plugin":
        if args.obsidian_plugin_command == "register":
            emit(register_obsidian_plugin(args.package.resolve()))
        elif args.obsidian_plugin_command == "deploy":
            emit(deploy_obsidian_plugin(args.out.resolve()))
        elif args.obsidian_plugin_command == "status":
            emit(obsidian_plugin_status(args.out.resolve() if args.out else None))
        else:
            emit(remove_obsidian_plugin(args.out.resolve()))
    elif args.command == "feedback":
        if args.feedback_command == "create":
            emit(
                create_feedback(
                    args.out.resolve(),
                    args.target,
                    args.start_line,
                    args.end_line,
                    args.comment.resolve(),
                    args.severity,
                    args.author,
                    args.source,
                )
            )
        elif args.feedback_command == "list":
            emit(list_feedback(args.out.resolve(), args.status))
        elif args.feedback_command == "locate":
            result = locate_feedback(args.out.resolve(), args.feedback)
            emit(result)
            return 0 if result.get("status") == "passed" else 5
        elif args.feedback_command == "resolve":
            emit(
                resolve_feedback(
                    args.out.resolve(),
                    args.feedback,
                    args.decision,
                    args.resolution.resolve(),
                    args.applied_record.resolve() if args.applied_record else None,
                )
            )
        else:
            result = audit_feedback(args.out.resolve())
            emit(result)
            return 0 if result.get("status") == "passed" else 5
    elif args.command == "workspace":
        if args.workspace_command == "sync":
            output = args.out.resolve()
            workspace = sync_workspace(output, args.repo.resolve())
            emit({**workspace, "machine": sync_workspace_changes(output)})
        elif args.workspace_command == "status":
            emit(workspace_status(args.out.resolve()))
        elif args.workspace_command == "session-start":
            emit(start_session(args.out.resolve(), args.repo.resolve(), args.question, args.budget, args.profile))
        elif args.workspace_command == "session-finish":
            emit(finish_session(args.out.resolve(), args.repo.resolve(), args.session, args.summary.resolve(), args.title))
        else:
            emit(sessions_status(args.out.resolve()))
    elif args.command == "agent-policy":
        if args.agent_policy_command == "install":
            emit(
                install_agent_protocol(
                    args.out.resolve(),
                    [path.resolve() for path in args.workspace_root],
                    python=args.python.resolve() if args.python else None,
                    ckb=args.ckb.resolve() if args.ckb else None,
                )
            )
        elif args.agent_policy_command == "check":
            result = audit_agent_protocol(args.out.resolve())
            emit(result)
            return 0 if result.get("status") == "passed" else 5
        else:
            emit(agent_protocol_status(args.out.resolve()))
    elif args.command == "automation":
        if args.automation_command == "register":
            emit(
                register_project(
                    args.repo,
                    args.out,
                    args.registry,
                    args.harness or None,
                    max_field_chars=args.max_field_chars,
                    custom_redactions=args.redact,
                    workspace_roots=args.workspace_root,
                )
            )
        elif args.automation_command == "unregister":
            emit(unregister_project(args.repo, args.registry))
        elif args.automation_command == "registry":
            emit(registry_status(args.registry))
        elif args.automation_command == "activate":
            emit(activate_skill_session(args.harness, args.session_id, args.cwd, args.registry, args.source))
        elif args.automation_command in {"ingest", "hook"}:
            try:
                raw_text = args.event.read_text(encoding="utf-8-sig") if args.event else sys.stdin.read()
                raw = json.loads(raw_text)
                result = ingest_event(args.harness, raw, args.registry)
                emit(result["hook_output"] if args.automation_command == "hook" else result)
            except Exception as exc:
                if args.automation_command != "hook":
                    raise
                print(f"CKB_AUTOMATION_HOOK_ERROR={type(exc).__name__}: {exc}", file=sys.stderr)
                emit({})
        elif args.automation_command == "drain":
            emit(drain_automation(args.out, args.limit))
        elif args.automation_command == "retry":
            emit(retry_failed_automation(args.out, args.limit))
        elif args.automation_command == "status":
            emit(automation_status(args.out))
        elif args.automation_command == "pending":
            emit(pending_automation_reviews(args.out, args.all))
        elif args.automation_command == "review":
            emit(review_automation(args.out, args.review))
        elif args.automation_command == "review-template":
            emit(write_automation_review_template(args.out, args.review_id, args.write))
        else:
            emit(render_integration(args.harness, args.destination, args.python, args.ckb, args.registry, force=args.force))
    elif args.command == "relink":
        emit(relink_sources(args.out.resolve(), args.repo_root.resolve(), args.editor, args.source_view, args.custom_template))
    elif args.command == "showcase":
        emit(package_showcase(args.dist.resolve(), args.sample))
    elif args.command == "page-config":
        if args.write:
            emit(write_page_config(args.write, DEFAULT_PAGE_CONFIG, overwrite=args.force))
        else:
            config, source = load_page_config(args.validate)
            emit({"schema_version": config["schema_version"], "status": "passed", "source": source, "sha256": page_config_sha256(config), "normalized": config})
    elif args.command == "runtime":
        if args.runtime_command == "plan":
            emit(deployment_plan())
        elif args.runtime_command == "deploy":
            emit(deploy_runtime(args.accept))
        elif args.runtime_command == "remove":
            emit(remove_runtime(args.lock_id))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CkbError as exc:
        print(f"CKB_ERROR={type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(exc.exit_code)
    except KeyboardInterrupt:
        print("CKB_ERROR=Interrupted", file=sys.stderr)
        raise SystemExit(130)
