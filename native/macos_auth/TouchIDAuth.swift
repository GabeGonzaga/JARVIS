import Foundation
import LocalAuthentication

let context = LAContext()
var error: NSError?

// Use .deviceOwnerAuthentication if you want fallback to macOS password.
// Use .deviceOwnerAuthenticationWithBiometrics if you want biometrics-only.
let policy = LAPolicy.deviceOwnerAuthentication

guard context.canEvaluatePolicy(policy, error: &error) else {
    fputs("TouchID unavailable: \(error?.localizedDescription ?? "unknown")\n", stderr)
    exit(2)
}

let sem = DispatchSemaphore(value: 0)
var ok = false

context.evaluatePolicy(policy, localizedReason: "Unlock JARVIS") { success, _ in
    ok = success
    sem.signal()
}

_ = sem.wait(timeout: .distantFuture)
exit(ok ? 0 : 1)
