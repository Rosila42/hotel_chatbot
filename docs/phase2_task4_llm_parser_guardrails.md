# Phase 2 — Task 4: Optional LLM Parser Guardrails

## Purpose

Introduce an optional `LLMParser` implementation of the existing parser contract without introducing an alternate execution path.

```text
raw text
   ↓
LLMParser
   ↓
CommandRequest | None
   ↓
ChatRouter
   ↓
authorization → validation → confirmation → execution
```

## Untrusted-output rule

LLM output is treated as untrusted input. The parser accepts only strict JSON with exactly:

```json
{
  "command": "COMMAND_NAME",
  "parameters": {}
}
```

The parser rejects malformed JSON, extra fields, unknown commands, non-string command names, and non-object parameters.

## Policy boundary

`LLMParser` does not:

- authorize users;
- decide permissions;
- decide confirmation requirements;
- call the PMS;
- call automation services;
- execute commands;
- mutate state.

It may normalize the command name and reject commands outside its explicitly supplied allow-list. It does not inspect command permissions.

## Provider isolation

The parser depends only on a minimal completion adapter protocol. No provider is configured by this task. The existing `LLMAdapter` remains unconfigured, and deterministic parsing remains the production path.

## Parameter validation

The parser deliberately does not duplicate the authoritative command-schema validation in `ChatRouter`. The router continues to validate the resulting `CommandRequest` against the command definition after authorization.

## Testing

Tests use a fake adapter and verify:

- valid structured output becomes `CommandRequest`;
- command names are normalized;
- unknown commands are rejected;
- policy/execution fields are rejected;
- malformed output is rejected;
- parser output contains no authorization or execution state;
- no provider-specific dependency is required.

## Production status

This task adds the optional adapter boundary only. The application is not switched from `DeterministicParser` to `LLMParser` by default.
