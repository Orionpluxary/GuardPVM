// =============================================================================
// FILE PURPOSE:
// Official Node.js / JavaScript client for the GuardPVM sandboxed execution engine.
// Spawns Python scripts via child_process, applies instruction limits and airbag modes,
// and parses execution telemetry JSON from stdout.
// Usage: const { GuardPVM } = require('./index.js');
// =============================================================================

const { spawn } = require('child_process');

/**
 * GuardPVM Node.js Client
 * Runs Python code in a sandboxed GuardPVM runtime with quotas and telemetry.
 */
class GuardPVM {
    /**
     * @param {Object} options
     * @param {number} [options.stepQuota=0] - Maximum VM bytecode steps allowed (0 = unlimited)
     * @param {('strict'|'recover')} [options.divMode='strict'] - Zero-division handling mode
     * @param {string} [options.pythonPath='/usr/local/bin/guard-python'] - Path to guard-python binary
     */
    constructor(options = {}) {
        this.stepQuota = options.stepQuota || 0;
        this.divMode = options.divMode || 'strict';
        this.pythonPath = options.pythonPath || '/usr/local/bin/guard-python';
    }

    /**
     * Executes Python code string.
     * @param {string} code - Python code to run
     * @param {Object} [overrideOptions={}] - Optional runtime overrides
     * @returns {Promise<{stdout: string, stderr: string, exitCode: number, stats: Object}>}
     */
    run(code, overrideOptions = {}) {
        const quota = overrideOptions.stepQuota !== undefined ? overrideOptions.stepQuota : this.stepQuota;
        const mode = overrideOptions.divMode || this.divMode;
        const pythonBin = overrideOptions.pythonPath || this.pythonPath;

        return new Promise((resolve) => {
            const wrapper = `
import sys, json

try:
    if hasattr(sys, 'set_div_mode'):
        sys.set_div_mode(${JSON.stringify(mode)})
    if hasattr(sys, 'set_step_quota') and ${quota} > 0:
        sys.set_step_quota(${quota})
    
    exec(${JSON.stringify(code)})
except BaseException as e:
    sys.stderr.write(f"GuardPVM Error: {type(e).__name__}: {e}\\n")
    sys.exit(1)
finally:
    if hasattr(sys, 'get_guard_stats'):
        stats = sys.get_guard_stats()
        print("__GUARDPVM_DELIMITER__")
        print(json.dumps(stats))
`;

            const env = { ...process.env };
            // Ensure any startup env quota is cleared so boot never fails
            delete env.GUARD_PVM_STEP_QUOTA;
            env.GUARD_PVM_DIV_MODE = mode;

            const proc = spawn(pythonBin, ['-c', wrapper], { env });

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (d) => { stdout += d.toString(); });
            proc.stderr.on('data', (d) => { stderr += d.toString(); });

            proc.on('close', (exitCode) => {
                let stats = {};
                let userOutput = stdout;

                if (stdout.includes('__GUARDPVM_DELIMITER__')) {
                    const parts = stdout.split('__GUARDPVM_DELIMITER__');
                    userOutput = parts[0].trim();
                    try {
                        stats = JSON.parse(parts[1].trim());
                    } catch (e) {
                        // ignore parse errors
                    }
                }

                resolve({
                    stdout: userOutput,
                    stderr: stderr.trim(),
                    exitCode: exitCode,
                    stats: stats
                });
            });
        });
    }
}

module.exports = { GuardPVM };
