import re
from pypdf import PdfReader
from os import makedirs, path, remove


def find_team(line):
    team_names = "Blackhawk|Cascade Mountain|Wilmot|Chestnut Mountain|Hidden Valley Ski Tea|Snowstar|Sundown Mountain|Four Lakes Racing|Tyrol Basin"  
    vals = re.findall(team_names, line, flags=re.IGNORECASE)
    return vals[0]


def find_racer(line, team):
    team_pos = line.index(team)
    return line[3:team_pos-1]


def extract_data(line, full_output):
    number = line[0:3]
    team_name = find_team(line)
    racer_name = find_racer(line, team_name)
    if full_output:
        racer = f"{number} {racer_name}|{team_name}"
    else:
        racer = f"{number} {racer_name}"
    return racer


def parse_pdf(filename, full_csv) -> dict:
    reader = PdfReader(filename)
    age_groups = {}
    racers = []

    current_group = None

    for page in reader.pages:
        text = page.extract_text()
        for line in text.split('\n'):
            if not (line.startswith('Bib') or line.startswith('Prelim') or line.startswith('Final') or line.startswith('Wisconsin')):
                if line.startswith('Girls -') or line.startswith('Boys -'):
                    if current_group != line:
                        age_groups[line] = []
                        current_group = line
                elif len(line.split('Girls -')) > 1 or len(line.split('Boys -')) > 1:
                    if len(line.split('Girls -')) > 1:
                        partial_line = line.partition('Girls -')
                    else:
                        partial_line = line.partition('Boys -')

                    header = partial_line[1] + partial_line[2]
                    entry = partial_line[0]
                    if current_group != header:
                        current_group = header
                        racers = []
                        racers.append(extract_data(entry, full_csv))
                        age_groups[current_group] = racers

                    else:
                        racers = age_groups[current_group]
                        racers.append(extract_data(entry, full_csv))
                else:
                    if not line.startswith('Printed') and not line.startswith('Grand Total'):
                        racers = age_groups[current_group]
                        racers.append(extract_data(line, full_csv))
    return age_groups


def build_outputs(age_group_recs, output_directory):
    full_output = path.join(output_directory, "Full_Output.csv")

    if path.exists(full_output):
        remove(full_output)

    for group, racers in age_group_recs.items():
        filename = f"{group}.csv"

        full_path = path.join(output_directory, filename)        
        with open(full_path, "w", encoding="utf-8",) as file:
            file.write("\n".join(racers))

        with open(full_output, "a", encoding="utf-8") as full_file:
            racers_with_age_group = [racer + f",'{group}'" for racer in racers]
            full_file.write("\n".join(racers_with_age_group))

            if group != list(age_group_recs.keys())[-1]:
                full_file.write("\n")


def run(filename: str, full_csv: bool):
    filename_without_extension = filename.split('.')[0]
    output_dir = f"output/{filename_without_extension}"
    makedirs(output_dir, exist_ok=True)
    recs = parse_pdf(filename, full_csv)
    build_outputs(recs, output_dir)


if __name__ == "__main__":
    run("CascadePreliminaryStartOrder.pdf", True)
