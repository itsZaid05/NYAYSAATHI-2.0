"""Read-only model availability probe. Does not assert account pricing or quota."""

from backend.providers import GeminiProvider, ProviderUnavailable

if __name__ == "__main__":
    try:
        for model in GeminiProvider().models():
            print(model.get("name"), model.get("supportedGenerationMethods"))
        print(
            "Separately review https://ai.google.dev/gemini-api/docs/pricing and account quotas/terms."
        )
    except ProviderUnavailable as exc:
        print(exc)
        raise SystemExit(1)
