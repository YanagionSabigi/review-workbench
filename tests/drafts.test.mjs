import test from "node:test";
import assert from "node:assert/strict";
import { restoreBackup, getItemDraft } from "../web/scripts/drafts.js";

test("restoring an old backup never upgrades its revision to the disk version", () => {
  const local = {
    package_id: "p",
    base_commit: "same",
    material_hash: "same",
    revision: 0,
    items: { a: { mode: "keep" } },
  };
  const remote = {
    package_id: "p",
    base_commit: "same",
    material_hash: "same",
    revision: 2,
    items: { b: { mode: "comment", comment: "另一页的新意见" } },
  };
  const result = restoreBackup(local, remote);
  assert.equal(result.drafts.revision, 0);
  assert.equal(result.needsComparison, true);
  assert.equal(remote.items.b.comment, "另一页的新意见");
});
test("same-version recovery is safe and creates an independent local copy", () => {
  const local = {
    package_id: "p",
    base_commit: "same",
    material_hash: "same",
    revision: 2,
    items: { a: { mode: "keep" } },
  };
  const result = restoreBackup(local, structuredClone(local));
  assert.equal(result.needsComparison, false);
  result.drafts.items.a.mode = "accept";
  assert.equal(local.items.a.mode, "keep");
});
test("item identifiers that match Object properties still get their own drafts", () => {
  const drafts = { items: {} };
  const value = getItemDraft(drafts, "constructor");
  assert.equal(value.mode, null);
  value.comment = "真实输入";
  assert.equal(drafts.items.constructor.comment, "真实输入");
});
