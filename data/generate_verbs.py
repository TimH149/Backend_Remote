zwakke_werkwoorden_file = "zwakke_werkwoorden.txt"
sterke_werkwoorden_file = "sterke_werkwoorden.txt"
output_file = "generated_werkwoorden.txt"

def read_zwakke_werkwoorden():
    with open(zwakke_werkwoorden_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines()]
    
def read_sterke_werkwoorden():
    with open(sterke_werkwoorden_file, "r", encoding="utf-8") as f:
        return [[word.strip() for word in line.split()] for line in f.readlines()]
    
def count_ending(werkwoord_infinitief, letters, max=2):
    count = 0
    for letter in reversed(werkwoord_infinitief):
        if letter in letters:
            count += 1
            if count >= max:
                break
        else:
            break
    return count

# infinitief, ik, jij, hij/zij/het, wij, jullie, zij
tegenwoordige_tijd_exceptions = {
    "zien": ["zien", "zie", "ziet", "ziet", "zien", "zien", "zien"],
    "zijn": ["zijn", "ben", "bent", "is", "zijn", "zijn", "zijn"],
    "gaan": ["gaan", "ga", "gaat", "gaat", "gaan", "gaan", "gaan"],
    "slaan": ["slaan", "sla", "slaat", "slaat", "slaan", "slaan", "slaan"],
    "doen": ["doen", "doe", "doet", "doet", "doen", "doen", "doen"],
    "duwen": ["duw", "duw", "duwt", "duwt", "duwen", "duwen", "duwen"],
    "fluisteren": ["fluisteren", "fluister", "fluistert", "fluistert", "fluisteren", "fluisteren", "fluisteren"],
    "tekenen": ["tekenen", "teken", "tekent", "tekent", "tekenen", "tekenen", "tekenen"],
    "regelen": ["regelen", "regel", "regelt", "regelt", "regelen", "regelen", "regelen"],
    "openen": ["openen", "open", "opent", "opent", "openen", "openen", "openen"],
    "hebben": ["hebben", "heb", "heeft", "heeft", "hebben", "hebben", "hebben"],
    "staan": ["staan", "sta", "staat", "staat", "staan", "staan", "staan"]
}

def generate_tegenwoordige_tijd(werkwoord_infinitief):
    if werkwoord_infinitief in tegenwoordige_tijd_exceptions:
        assert len(tegenwoordige_tijd_exceptions[werkwoord_infinitief]) == 7, f"Expected 7 forms for {werkwoord_infinitief}, got {len(tegenwoordige_tijd_exceptions[werkwoord_infinitief])}: {tegenwoordige_tijd_exceptions[werkwoord_infinitief]}"
        return tegenwoordige_tijd_exceptions[werkwoord_infinitief]

    klinkers = "aeiou"
    medeklinkers = "bcdfghklmnpqrstvwxyz"

    #inf_endswith_elen = werkwoord_infinitief.endswith("elen")
    #inf_endswith_enen = werkwoord_infinitief.endswith("enen")

    stam = werkwoord_infinitief[:-2]
    trailing_medeklinkers_count = count_ending(stam, medeklinkers, max=2)
    medeklinkers_trailing = stam[-trailing_medeklinkers_count:]
    rest = stam[:len(stam)-trailing_medeklinkers_count]
    klinker_count = count_ending(rest, klinkers)
    is_ij = rest.endswith("ij")
    if is_ij:
        klinker_count = 2

    transformed_medeklinkers = {
        "v": "f",
        "z": "s",
    }

    if trailing_medeklinkers_count == 2:
        medeklinkers_are_different = medeklinkers_trailing[0] != medeklinkers_trailing[1]
        if medeklinkers_are_different:
            second_medeklinker = medeklinkers_trailing[1]
            if second_medeklinker in transformed_medeklinkers:
                second_medeklinker = transformed_medeklinkers[second_medeklinker]
                
            stam = rest + medeklinkers_trailing[0] + second_medeklinker
        else:
            # double medeklinker means we likely remove one 
            stam = stam[:-1]
    elif trailing_medeklinkers_count == 1:

        medeklinker = medeklinkers_trailing[0]

        if medeklinker in transformed_medeklinkers:
            medeklinker = transformed_medeklinkers[medeklinker]
        medeklinkers_trailing = [medeklinker]
        stam = rest + medeklinker
        
        # double the klinker if there is one
        #if klinker_count == 1 and not (inf_endswith_elen or inf_endswith_enen):
        if klinker_count == 1:
            doubled_klinkers = "aeuo"
            if rest[-1] in doubled_klinkers:
                stam = rest + rest[-1] + medeklinker

    stam_ends_with_t = stam.endswith("t")

    if stam_ends_with_t:
        jij = stam
        hij_zij_het = stam
    else:
        jij = stam + "t"
        hij_zij_het = stam + "t"

    
    wij = werkwoord_infinitief
    jullie = werkwoord_infinitief
    zij = werkwoord_infinitief
    return [werkwoord_infinitief, stam, jij, hij_zij_het, wij, jullie, zij]

def generate_verleden_tijd(stam):
    het_fokschaap = "het sexy fokschaap"

    laatste_letter = stam[-1]
    verlengde_letter = "t" if laatste_letter in het_fokschaap else "d"
    verleden_tijd = stam + verlengde_letter + "e"
    verleden_tijd_meervoud = stam + verlengde_letter + "en"
    
    if laatste_letter == verlengde_letter:
        stam = stam[:-1]
    voltooid_deelwoord = "ge" + stam + verlengde_letter
    return verleden_tijd, verleden_tijd_meervoud, voltooid_deelwoord
    
werkwoorden = []

# infinitief, stam, jij,, hij/zij/het, wij, jullie, zij, verleden tijd, verleden tijd meervoud, voltooid deelwoord

zwakke_werkwoorden = read_zwakke_werkwoorden()
sterke_werkwoorden = read_sterke_werkwoorden()
sterke_werkwoorden_infinitieven = [werkwoord[0] for werkwoord in sterke_werkwoorden]

for werkwoord in sterke_werkwoorden:
    infinitief = werkwoord[0]
    tegenwoordige_tijd = generate_tegenwoordige_tijd(infinitief).copy()

    verleden_tijd = werkwoord[1]
    verleden_tijd_meervoud = werkwoord[2]
    voltooid_deelwoord = werkwoord[3]
    tegenwoordige_tijd.append(verleden_tijd)
    tegenwoordige_tijd.append(verleden_tijd_meervoud)
    tegenwoordige_tijd.append(voltooid_deelwoord)

    werkwoorden.append(tegenwoordige_tijd)

for werkwoord in zwakke_werkwoorden:
    if werkwoord in sterke_werkwoorden_infinitieven:
        continue
    infinitief = werkwoord
    tegenwoordige_tijd = generate_tegenwoordige_tijd(infinitief).copy()
    stam = tegenwoordige_tijd[1]

    verleden_tijd, verleden_tijd_meervoud, voltooid_deelwoord = generate_verleden_tijd(stam)
    tegenwoordige_tijd.append(verleden_tijd)
    tegenwoordige_tijd.append(verleden_tijd_meervoud)
    tegenwoordige_tijd.append(voltooid_deelwoord)

    werkwoorden.append(tegenwoordige_tijd)

generate_tegenwoordige_tijd("blijven")

with open(output_file, "w", encoding="utf-8") as f:
    for werkwoord in werkwoorden:
        f.write("\t".join(werkwoord) + "\n")