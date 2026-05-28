from ddgs import DDGS

def web_search(query:str, max_results:int=3)->str:
    print(f"[Tool] Scraping web for: {query}")
    try:
        res = []
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            if not results:
                return "Query returned no results."
            else:
                for r in results:
                    res.append(f"Title: {r.get('title')}\nSummary: {r.get('body')}\nURL: {r.get('href')}\n")

        return "\n".join(res)

    except Exception as e:
        return f"Web-search failed withe error: {e}"

if __name__ == "__main__":
    print(web_search("SpaceX"))