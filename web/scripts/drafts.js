export function restoreBackup(local, remote) {
  if (
    local.package_id !== remote.package_id ||
    local.base_commit !== remote.base_commit ||
    local.material_hash !== remote.material_hash
  ) {
    throw new Error("备份属于另一轮材料，不能恢复到当前审核包");
  }
  return {
    drafts: structuredClone(local),
    needsComparison: local.revision !== remote.revision,
  };
}

export function getItemDraft(drafts, id) {
  if (!Object.hasOwn(drafts.items, id))
    drafts.items[id] = {
      mode: null,
      edits: {},
      touched: false,
      comment: "",
      quotes: [],
    };
  return drafts.items[id];
}
