import tkinter as tk
from tkinter import filedialog
from difflib import SequenceMatcher
import re
import xml.etree.ElementTree as ET
import os

def select_files():
    root = tk.Tk()
    root.withdraw()
    
    srt_file = filedialog.askopenfilename(title="SRT dosyanızı seçin", filetypes=[("Subtitle Files", "*.srt")])
    video_file = filedialog.askopenfilename(title="Video dosyanızı seçin", filetypes=[("Video Files", "*.mp4;*.mkv;*.avi;*.mov")])
    
    return srt_file, video_file

def parse_srt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    
    subtitles = []
    text = ""
    timestamp = None
    for line in lines:
        if line.strip().isdigit():
            if text and timestamp:
                subtitles.append((timestamp, text.strip()))
                text = ""
        elif "-->" in line:
            timestamp = parse_timestamp(line.strip())
        else:
            text += " " + line.strip()
    if text and timestamp:
        subtitles.append((timestamp, text.strip()))
    
    return subtitles

def parse_timestamp(timestamp_line):
    match = re.search(r"(\d{2}):(\d{2}):(\d{2}),\d{3}", timestamp_line)
    if match:
        hours, minutes, seconds = map(int, match.groups())
        return hours * 3600 + minutes * 60 + seconds
    return None

def find_similar_sentences(subtitles, threshold=0.7, time_window=180):
    similar_segments = []
    processed_indices = set()
    
    for i in range(len(subtitles)):
        if i in processed_indices:
            continue
        segment_start = subtitles[i][0]
        segment_end = subtitles[i][0]
        
        for j in range(i + 1, len(subtitles)):
            similarity = SequenceMatcher(None, subtitles[i][1], subtitles[j][1]).ratio()
            time_diff = subtitles[j][0] - segment_end
            
            if similarity >= threshold and time_diff <= time_window:
                segment_end = subtitles[j][0]
                processed_indices.add(j)
            else:
                break
        
        if segment_start != segment_end:
            similar_segments.append((segment_start, segment_end))
    
    return similar_segments

def create_premiere_xml(video_path, cut_segments, output_xml):
    root = ET.Element("xmeml", version="4")
    sequence = ET.SubElement(root, "sequence")
    media = ET.SubElement(sequence, "media")
    video = ET.SubElement(media, "video")
    track = ET.SubElement(video, "track")
    
    for cut_start, cut_end in cut_segments:
        clipitem = ET.SubElement(track, "clipitem")
        file_elem = ET.SubElement(clipitem, "file")
        path_elem = ET.SubElement(file_elem, "pathurl")
        path_elem.text = f"file://{video_path}"
        
        in_elem = ET.SubElement(clipitem, "in")
        in_elem.text = str(cut_start)
        out_elem = ET.SubElement(clipitem, "out")
        out_elem.text = str(cut_end)
    
    tree = ET.ElementTree(root)
    tree.write(output_xml, encoding="utf-8", xml_declaration=True)

def main():
    srt_path, video_path = select_files()
    if srt_path:
        subtitles = parse_srt(srt_path)
        similar_segments = find_similar_sentences(subtitles, threshold=0.7, time_window=180)
        
        if similar_segments:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            output_xml = os.path.join(desktop_path, "cut_project.xml")
            create_premiere_xml(video_path, similar_segments, output_xml)

if __name__ == "__main__":
    main()
