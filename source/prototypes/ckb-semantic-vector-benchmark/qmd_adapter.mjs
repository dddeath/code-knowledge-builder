import { readFile } from "node:fs/promises";
import { basename, join } from "node:path";
import { pathToFileURL } from "node:url";


function parseArguments(values) {
  const result = {};
  for (let index = 0; index < values.length; index += 2) {
    const key = values[index];
    const value = values[index + 1];
    if (!key?.startsWith("--") || value === undefined) {
      throw new Error(`invalid argument sequence near ${key ?? "<end>"}`);
    }
    result[key.slice(2)] = value;
  }
  return result;
}


function requireArgument(arguments_, name) {
  const value = arguments_[name];
  if (!value) {
    throw new Error(`missing --${name}`);
  }
  return value;
}


async function loadSdk(packageRoot) {
  const packageJson = JSON.parse(
    await readFile(join(packageRoot, "package.json"), "utf8"),
  );
  const buildInfo = JSON.parse(
    await readFile(join(packageRoot, "dist", "cli", "build-info.json"), "utf8"),
  );
  const sdk = await import(pathToFileURL(join(packageRoot, "dist", "index.js")).href);
  return { packageJson, buildInfo, sdk };
}


function config(collection, corpus, model) {
  return {
    global_context: "",
    collections: {
      [collection]: {
        path: corpus,
        pattern: "*.md",
        includeByDefault: false,
      },
    },
    models: { embed: model },
  };
}


function identity(packageJson, buildInfo) {
  return {
    package_name: packageJson.name,
    package_version: packageJson.version,
    build_commit: buildInfo.commit,
    node_version: process.version,
  };
}


async function build(arguments_) {
  const packageRoot = requireArgument(arguments_, "package-root");
  const dbPath = requireArgument(arguments_, "db");
  const corpus = requireArgument(arguments_, "corpus");
  const collection = requireArgument(arguments_, "collection");
  const model = requireArgument(arguments_, "model");
  const expectedDocuments = Number(requireArgument(arguments_, "expected-documents"));
  const { packageJson, buildInfo, sdk } = await loadSdk(packageRoot);
  const store = await sdk.createStore({
    dbPath,
    config: config(collection, corpus, model),
  });
  const started = performance.now();
  try {
    const update = await store.update({ collections: [collection] });
    const embed = await store.embed({
      collection,
      model,
      maxDocsPerBatch: 64,
      maxBatchBytes: 64 * 1024 * 1024,
      chunkStrategy: "regex",
    });
    const status = await store.getStatus();
    const collections = await store.listCollections();
    const selected = collections.find((item) => item.name === collection);
    const payload = {
      schema_version: 1,
      kind: "qmd-build",
      identity: identity(packageJson, buildInfo),
      collection,
      expected_documents: expectedDocuments,
      indexed_documents: selected?.active_count ?? null,
      update,
      embed,
      status,
      wall_ms: Number((performance.now() - started).toFixed(6)),
    };
    process.stdout.write(`${JSON.stringify(payload)}\n`);
  } finally {
    await store.close();
  }
}


async function query(arguments_) {
  const packageRoot = requireArgument(arguments_, "package-root");
  const dbPath = requireArgument(arguments_, "db");
  const corpus = requireArgument(arguments_, "corpus");
  const collection = requireArgument(arguments_, "collection");
  const model = requireArgument(arguments_, "model");
  const questionId = requireArgument(arguments_, "question-id");
  const question = requireArgument(arguments_, "question");
  const candidateDepth = Number(requireArgument(arguments_, "candidate-depth"));
  const hotRuns = Number(requireArgument(arguments_, "hot-runs"));
  const { packageJson, buildInfo, sdk } = await loadSdk(packageRoot);
  const store = await sdk.createStore({
    dbPath,
    config: config(collection, corpus, model),
  });
  try {
    for (let runIndex = 0; runIndex <= hotRuns; runIndex += 1) {
      const started = performance.now();
      const results = await store.searchVector(question, {
        limit: candidateDepth,
        collection,
      });
      const payload = {
        schema_version: 1,
        kind: "qmd-query",
        identity: identity(packageJson, buildInfo),
        question_id: questionId,
        cache_state: runIndex === 0 ? "cold" : "hot",
        run_index: runIndex === 0 ? 1 : runIndex,
        latency_ms: Number((performance.now() - started).toFixed(6)),
        results: results.map((item) => ({
          file: basename(item.filepath),
          filepath: item.filepath,
          score: item.score,
          source: item.source,
          chunk_pos: item.chunkPos,
        })),
      };
      process.stdout.write(`${JSON.stringify(payload)}\n`);
    }
  } finally {
    await store.close();
  }
}


const [command, ...rest] = process.argv.slice(2);
const arguments_ = parseArguments(rest);
if (command === "build") {
  await build(arguments_);
} else if (command === "query") {
  await query(arguments_);
} else {
  throw new Error(`unknown command: ${command ?? "<missing>"}`);
}
