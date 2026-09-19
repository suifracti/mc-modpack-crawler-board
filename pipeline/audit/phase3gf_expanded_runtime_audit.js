/**
 * Compatibility entry point for the Phase 3G-F.3-A expanded audit.
 *
 * The implementation lives in phase3gf_independent_safety_audit.js so the
 * independence contract is explicit and can be exercised without invoking
 * the candidate runtime. Keep this filename for existing handoff commands.
 */
const audit = require('./phase3gf_independent_safety_audit.js');

if (require.main === module) audit.main();

module.exports = audit;
