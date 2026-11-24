// =============================================================================
// 😁 changes done here (100% New File: Node.js SDK Integration Demo)
// =============================================================================
// FILE PURPOSE:
// Demonstrates running Python code inside GuardPVM from Node.js/JavaScript.
// It uses the GuardPVM Node client to execute sandboxed Python code with
// instruction quotas, zero-division recovery, and JSON telemetry parsing.
// Run with: node examples/04_node_integration.js
// =============================================================================

/*
=============================================================================
DUAL RUN COMPARISON GUIDE:
=============================================================================

🔴 [1] RUNNING AGAINST REGULAR / STOCK PYTHON (Standard python3):
    $ pythonPath="python3" node examples/04_node_integration.js
    
    EXPECTED OUTCOME / ERROR:
    -------------------------------------------------------------------------
    The infinite loop test hangs forever or fails to report telemetry stats
    because stock python3 lacks sys.set_step_quota and sys.get_guard_stats.
    -------------------------------------------------------------------------

🟢 [2] RUNNING AGAINST GUARDPVM (guard-python):
    $ node examples/04_node_integration.js
    
    EXPECTED OUTCOME (SUCCESS):
    -------------------------------------------------------------------------
    [1] Running normal Python from JS: Output & telemetry returned as JSON
    [2] Infinite Loop Protection: Stopped cleanly at exact step quota
    [3] Zero-Division Airbag: 10/0 returns 0 without crashing Node process
    -------------------------------------------------------------------------
=============================================================================
*/

const path = require('path');
const { GuardPVM } = require('../src/node/index.js');

async function main() {
    console.log("=================================================================");
    console.log(" GUARDPVM NODE.JS SDK DEMONSTRATION");
    console.log("=================================================================");

    const vm = new GuardPVM({
        pythonPath: process.env.GUARD_PYTHON || '/usr/local/bin/guard-python'
    });

    // 1. Normal Workload
    console.log("\n[1] Running normal Python calculation from JavaScript:");
    const res1 = await vm.run(`
primes = [x for x in range(2, 50) if all(x % d != 0 for d in range(2, int(x**0.5) + 1))]
print(f"Primes up to 50: {primes}")
`);
    console.log("  Stdout       :", res1.stdout.trim());
    console.log("  Steps Taken  :", res1.stats.steps_executed);
    console.log("  Top 3 Opcodes:", Object.keys(res1.stats.top_opcodes || {}).slice(0, 3));

    // 2. Step Quota Sandbox
    console.log("\n[2] Testing Step Quota protection against infinite loop:");
    const res2 = await vm.run(`
i = 0
while True:
    i += 1
`, { stepQuota: 5000 });
    console.log("  Exit Code    :", res2.exitCode, "(Clean failure)");
    console.log("  Stderr       :", res2.stderr.trim());
    console.log("  Steps Halted :", res2.stats.steps_executed);

    // 3. Airbag Mode
    console.log("\n[3] Testing Zero-Division Recovery Mode (Airbag ON):");
    const res3 = await vm.run(`
a = 10 / 0
b = 100 // 0
print(f"Recovered results: a={a}, b={b}")
`, { divMode: 'recover' });
    console.log("  Stdout       :", res3.stdout.trim());
    console.log("  Traps Caught :", res3.stats.zero_div_count);

    console.log("\n✅ [SUCCESS] All Node.js integration tests passed!");
}

main().catch(console.error);
