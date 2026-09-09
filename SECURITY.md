# Security Policy

Standard Astro is a research-alpha workbench. Security reports are welcome,
including reports where a technical flaw could silently weaken a scientific
provenance, evidence, or claim-validation gate.

## Supported versions

Only the latest revision on the default branch and the currently operated
deployment are considered for fixes. The project does not currently promise
backports or long-term support for older commits, forks, or deployments.

## Reporting a vulnerability

GitHub's private vulnerability-reporting flow (repository **Security** tab)
is not enabled for this repository as of 2026-09-09. Until it is, open a
public issue containing only a request for a private maintainer contact. Keep
all vulnerability details out of that issue: do not include secrets, personal
data, unpublished research data, or working exploit details. If the private
flow is enabled later, use it instead. This repository does not publish a
dedicated security email address at present.

Please include, where applicable:

- the affected commit, endpoint, component, and deployment mode;
- a minimal reproduction and the expected versus observed result;
- the security or scientific-integrity impact;
- whether credentials, personal data, or unpublished results may be exposed;
- a suggested mitigation, if you have one.

Response timing is best effort and is not currently covered by a service-level
commitment. Please allow a reasonable remediation and release window before
public disclosure.

## Important security boundaries

- Hosted production must keep arbitrary Python execution disabled. The legacy
  in-process and subprocess executors are crash-containment mechanisms, not OS
  security sandboxes.
- The local Codex/Claude subscription-CLI bridges and Bot Console are for a
  trusted, single-user machine. They are rejected in production and must not be
  exposed as a multi-user remote execution service.
- Model output is untrusted. Numerical and bibliographic claims become
  trustworthy only through the backend's registered tools, provenance records,
  and validation gates.
- API keys and signing/encryption secrets must not be committed. Production
  JWT, Fernet, and evidence-signing keys must be retained in an external secret
  manager so backup recovery remains possible.

Reports about authentication or authorization bypass, secret disclosure,
remote code execution, path traversal, cross-user data access, dependency or
deployment compromise, and reproducible scientific-gate bypasses are in scope.
Provider outages, unsupported connectors that already fail closed, social
engineering, and findings without a reproducible impact are normally out of
scope.

There is currently no paid bug-bounty program.
