from providers.base_provider import BrowserAIProvider


class ChatGPTBrowserProvider(BrowserAIProvider):
    id = "chatgpt_web"
    label = "ChatGPT Web"
    url = "https://chatgpt.com/"
    login_url = "https://chatgpt.com/"
    prompt_selectors = (
        "#prompt-textarea",
        "textarea[data-testid='prompt-textarea']",
        "div[contenteditable='true'][data-testid='prompt-textarea']",
        "div[contenteditable='true']",
        "textarea",
    )
    submit_selectors = (
        "button[data-testid='send-button']",
        "button[aria-label*='Send' i]",
        "form button[type='submit']",
    )
    response_selectors = (
        "[data-message-author-role='assistant']",
        "article:has([data-message-author-role='assistant'])",
        ".markdown",
    )
    logged_out_markers = ("log in", "sign up", "continue with google")
