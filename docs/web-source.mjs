import { identityMapping } from "./web-core.mjs";

/** Commit a parsed, fingerprinted table only if it is still the latest choice. */
export async function replaceSource(state, workflow, index, read) {
  const current = state[workflow];
  const slot = workflow === "audit" ? 0 : index;
  const token = Symbol();
  current.tokens ??= [];
  current.tokens[slot] = token;
  const isCurrent = () => state[workflow] === current && current.tokens[slot] === token;

  try {
    const source = await read();
    if (!isCurrent()) return false;
    const mapping = identityMapping(source.table.headers);
    if (workflow === "audit") {
      current.source = source;
      current.mapping = mapping;
    } else {
      current.sources[index] = source;
      current.mappings[index] = mapping;
      current.decisions = [];
    }
    current.result = null;
    return true;
  } catch (error) {
    if (isCurrent()) throw error;
    return false;
  }
}
