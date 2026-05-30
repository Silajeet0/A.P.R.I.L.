import requests
from bs4 import BeautifulSoup

def page_content(url:str)->str:
    print(f"[Tool] Checking : {url} for more details")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        return f"URL: {url}, \nContent: Failed to fetch webpage. Error: {e}"
    
    soup = BeautifulSoup(html_content, "html.parser")

    to_decompose = soup.find_all(["script", "style", "header", "footer", "nav", "aside"])
    
    for garbage in to_decompose:
        garbage.decompose()

    p_tags = soup.find_all("p")
    text_chunks = [p.get_text(strip=True) for p in p_tags]
    content = " ".join(text_chunks)

    if len(content) > 3500:
        trimmed_content = content[:3500] + "...[Text truncated by system]"
    else:
        trimmed_content = content
    return trimmed_content if trimmed_content else "No readable content on this page."

if __name__ == "__main__":
    print(page_content("https://www.geeksforgeeks.org/python/string-slicing-in-python/"))