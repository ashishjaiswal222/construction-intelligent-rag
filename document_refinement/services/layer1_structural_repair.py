import re
from typing import Tuple, List

class Layer1StructuralRepair:
    def repair(self, text: str) -> Tuple[str, List[str]]:
        """
        Layer 1: Structural Repair
        Fixes:
          - Line ending without [.!?:;)] + next line starts lowercase -> merge with space
          - word-\\nnext -> wordnext (strip hyphen, merge)
          - 3+ blank lines -> exactly 2 blank lines
          - Lines that are ONLY digits (page numbers) -> remove
          - Lines < 40 chars matching 'Page X of Y' pattern -> remove
        """
        fixes = []
        original_text = text
        
        # Split into lines
        lines = text.split('\n')
        
        # 1. Remove lone digits & Page X of Y footers
        filtered_lines = []
        for line in lines:
            s_line = line.strip()
            
            # Line is only digits
            if s_line.isdigit():
                fixes.append("removed_lone_page_number_line")
                continue
                
            # Line is < 40 chars and matches Page X of Y
            if len(s_line) < 40 and re.match(r'^page\s+\d+\s+of\s+\d+$', s_line, re.IGNORECASE):
                fixes.append("removed_page_x_of_y_footer")
                continue
                
            filtered_lines.append(line)
            
        # 2. Merge broken sentences and hyphenated line breaks
        merged_lines = []
        i = 0
        while i < len(filtered_lines):
            line = filtered_lines[i]
            
            if i + 1 < len(filtered_lines):
                next_line = filtered_lines[i+1].lstrip()
                
                # Check hyphenated word
                if line.endswith('-') and next_line and not next_line[0].isupper() and not next_line.startswith('-'):
                    line = line[:-1] + next_line
                    fixes.append("fixed_hyphenated_line_break")
                    i += 2
                    
                    # Continue merging if next lines are also broken
                    while i < len(filtered_lines):
                        n_line = filtered_lines[i].lstrip()
                        if line.endswith('-') and n_line and not n_line[0].isupper():
                            line = line[:-1] + n_line
                            i += 1
                        elif not re.search(r'[.!?:;)]\s*$', line) and n_line and n_line[0].islower() and not n_line.startswith('-'):
                            line = line + " " + n_line
                            i += 1
                        else:
                            break
                    merged_lines.append(line)
                    continue

                # Check broken sentence (no end punctuation, next line is lowercase)
                # Ensure it's not a list item starting with dash
                if not re.search(r'[.!?:;)]\s*$', line.rstrip()) and next_line and next_line[0].islower() and not next_line.startswith('-'):
                    line = line.rstrip() + " " + next_line
                    fixes.append("merged_broken_sentence_lowercase_start")
                    i += 2
                    
                    while i < len(filtered_lines):
                        n_line = filtered_lines[i].lstrip()
                        if not re.search(r'[.!?:;)]\s*$', line.rstrip()) and n_line and n_line[0].islower() and not n_line.startswith('-'):
                            line = line.rstrip() + " " + n_line
                            i += 1
                        else:
                            break
                    merged_lines.append(line)
                    continue
                    
            merged_lines.append(line)
            i += 1
            
        # 3. Collapse 3+ blank lines to exactly 2
        text_joined = '\n'.join(merged_lines)
        text_repaired = re.sub(r'\n{4,}', '\n\n\n', text_joined) # 4+ newlines means 3+ blank lines
        if text_repaired != text_joined:
            fixes.append("collapsed_four_blank_lines_to_two")
            
        return text_repaired, list(set(fixes))
