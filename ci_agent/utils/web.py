import requests
import re

class FireCrawler:
    def __init__(self, server_url: str):
        self.url = server_url
    
    def _clean_markdown(self, markdown_text):
        cleaned_lines = []
        seen_content = set()
        
        # Regex patterns to remove image links and long-form links
        image_link_pattern = re.compile(r'!\[.*?\]\(.*?\)')  # Matches ![alt](url)
        standalone_link_pattern = re.compile(r'^https?://\S+$')  # Matches full-line URLs
        inline_link_pattern = re.compile(r'\[.*?\]\(https?://.*?\)')  # Matches [text](url)
        
        lines = markdown_text.split('\n')
        
        for line in lines:
            line = image_link_pattern.sub('', line)  # Remove image links
            line = inline_link_pattern.sub('', line)  # Remove inline links
            
            # Skip empty lines or just dashes
            if not line.strip() or line.strip() == '-' * len(line.strip()):
                continue
            
            # Skip standalone URLs
            if standalone_link_pattern.match(line.strip()):
                continue
            
            # Keep headers and text content
            if line.strip().startswith('#') or line.strip():
                # Check for duplicate content
                if line.strip() not in seen_content:
                    cleaned_lines.append(line.strip())
                    seen_content.add(line.strip())
        
        return '\n'.join(cleaned_lines)
    
    def scrape(self, url):
        payload = {
            "url":  url,
            "formats": ["markdown"],
            # "onlyMainContent": True,
            # "includeTags": ["<body>"],
            # "excludeTags": ["<string>"],
            # "headers": {},
            # "waitFor": 0,
            # "mobile": False,
            # "skipTlsVerification": False,
            # "timeout": 30000,
            # "actions": [
            #     {
            #         "type": "wait",
            #         "selector": "#my-element"
            #     }
            # ],
            # "location": {
            #     "country": "US",
            #     "languages": ["en-US"]
            # },
            "removeBase64Images": True,
            "blockAds": True,
            "proxy": "basic"
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.request("POST", f"{self.url}/v1/scrape", json=payload, headers=headers)
        if response.status_code == 200:
            dictionary = response.json()
            markdown = dictionary["data"]["markdown"]
            return self._clean_markdown(markdown)
        return "Something went wrong"

#### TESTING
if __name__ == "__main__":
    f = FireCrawler("http://localhost:3002")
    response = f.scrape("https://icon.me/")
    print(response)