from ddgs import DDGS

def web_search(query:str, max_results:int=3)->str:
    print(f"[Tool] Scraping web for: {query}")
    try:
        formatted_results= []
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            if not results:
                return "Query returned no results."
            for idx, r in enumerate(results[:3]): 
                # STARVE THE SNIPPETS: Only extract Title and URL
                title = r.get('title')
                url = r.get('href')
                
                formatted_results.append(f"[{idx}] TITLE: {title}\nURL: {url}\n")

        return "\n".join(formatted_results)
        
        return "\n".join(formatted_results)

    except Exception as e:
        return f"Web-search failed withe error: {e}"

if __name__ == "__main__":
    print(web_search("SpaceX"))