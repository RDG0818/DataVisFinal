"""Download a university's publicly shared Box file using its public preview token."""
import argparse, re, requests
from pathlib import Path

def download(url, output):
    session=requests.Session()
    page=session.get(url,timeout=20);page.raise_for_status()
    match=re.search(r'preview_prefetch_token_map\\?":\{\\?"(\d+)\\?":\{\\?"read\\?":\\?"([^\\"]+)',page.text)
    if not match:raise ValueError('Public preview file id/token absent')
    file_id,token=match.groups()
    response=session.get(f'https://public.boxcloud.com/api/2.0/files/{file_id}/content',
                         headers={'Authorization':f'Bearer {token}'},timeout=45)
    response.raise_for_status()
    if not response.content.startswith((b'%PDF',b'PK\x03\x04')):raise ValueError('Unexpected binary type')
    Path(output).write_bytes(response.content)
    print(output,len(response.content))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('url');parser.add_argument('output');args=parser.parse_args()
    download(args.url,args.output)
