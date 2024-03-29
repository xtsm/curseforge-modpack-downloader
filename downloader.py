#!/usr/bin/env python3
import aiohttp
import argparse
import asyncio
import json
import sys
import os


async def download_file(sess, file_id, output_dir, no_cache):
  pid = file_id["projectID"]
  fid = file_id["fileID"]
  api_url = f"https://www.curseforge.com/api/v1/mods/{pid}/files/{fid}"
  async with sess.get(api_url) as req:
    file_info = await req.json()

  file_name = file_info["data"]["fileName"]
  file_length = file_info["data"]["fileLength"]
  file_path = os.path.join(output_dir, file_name)

  use_cache = not no_cache and os.path.isfile(file_path) and os.path.getsize(file_path) == file_length
  if not use_cache:
    download_url = f"https://www.curseforge.com/api/v1/mods/{pid}/files/{fid}/download"
    async with sess.get(download_url) as req:
      file_contents = await req.read()
    assert len(file_contents) == file_length
    with open(file_path, "wb") as f:
      f.write(file_contents)

  return file_name, file_length, use_cache


async def main():
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument("-m", "--manifest", help="path to manifest file (default is stdin)")
  arg_parser.add_argument("-o", "--output-dir", default="", help="path to output directory (default is current directory)")
  arg_parser.add_argument("-n", "--no-cache", action="store_true", help="redo download even if file already exists and has the correct size")
  args = arg_parser.parse_args()

  if args.manifest is None:
    manifest = json.load(sys.stdin)
  else:
    with open(args.manifest) as f:
      manifest = json.load(f)

  files = manifest["files"]
  completed = 0

  async with aiohttp.ClientSession() as sess:
    coros = [download_file(sess, f, args.output_dir, args.no_cache) for f in files]
    # freezes sometimes but if you're desperate, you can use it, might speed things up
    # for coro in asyncio.as_completed(coros):
    for coro in coros:
      filename, length, used_cache = await coro
      completed += 1
      print(f"[{completed}/{len(files)}] {filename} ({length}B{' cached' if used_cache else ''})")


if __name__ == "__main__":
  asyncio.run(main())
