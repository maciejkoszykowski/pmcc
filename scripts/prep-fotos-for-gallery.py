"""Przygotowanie zdjęć do galerii PMCC.

Użycie (z dowolnego folderu):
    python scripts/prep-fotos-for-gallery.py 2025
    python scripts/prep-fotos-for-gallery.py          <- skrypt zapyta o rok

Skąd i dokąd:
    oryginały:  tmp/galeria/ROK/
    wynik:      static/galeria/ROK/thumbnails/N_thumb.jpg
                static/galeria/ROK/web/N.jpg

Kroki:
    1. raport: image_count z data/galeria.yml vs. pliki w static/galeria/ROK/ (tylko ostrzega)
    2. jeśli static/galeria/ROK/ ma już zdjęcia, pytanie:
         [n]adpisz  — cały rok od nowa, nowa losowa kolejność (trzeba wgrać cały folder roku)
         [d]opisz   — stare zdjęcia bez zmian, nowe dostają kolejne numery (wgrać tylko nowe pliki)
         [p]rzerwij — nic nie zmienia
       Przy dopisywaniu skrypt sam rozpoznaje, które oryginały są już w galerii (porównuje obraz
       z plikami web/), więc do tmp/galeria/ROK/ można dorzucać nowe zdjęcia obok starych.
    3. zdjęcia w losowej kolejności -> miniatury (600 px) i wersje web (1200 px)
    4. wpisanie nowego image_count do data/galeria.yml
"""
import argparse
import os
import random
import re
import shutil
import sys

from PIL import Image, ImageOps, UnidentifiedImageError

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_OK = True
except ImportError:
    HEIF_OK = False

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.join(ROOT, "tmp", "galeria")
OUT_ROOT = os.path.join(ROOT, "static", "galeria")
DATA_FILE = os.path.join(ROOT, "data", "galeria.yml")

THUMB_SIZE = (600, 600)
WEB_SIZE = (1200, 1200)
JPEG_QUALITY = 85

# rozpoznawanie oryginałów, które już są w galerii: "odcisk" 16x16 (średnia jasność)
# zmierzone 2026-09-30 na 2025: ten sam obraz <= 5 różnic na 256, różne zdjęcia >= 12
HASH_SIZE = 16
SAME_PHOTO_MAX_DIFF = 8


def ask(question):
    try:
        return input(question).strip()
    except EOFError:
        return ""


def read_data():
    # newline="" zachowuje końce linii CRLF z pliku
    with open(DATA_FILE, encoding="utf-8", newline="") as f:
        return f.read()


def gallery_items(text):
    """Zwraca listę (title, image_count) z sekcji `item` w galeria.yml."""
    items = []
    for m in re.finditer(r"-\s*title\s*:\s*\"?([^\"\r\n#]+?)\"?\s*\r?\n\s*image_count\s*:\s*(\d+)", text):
        items.append((m.group(1).strip(), int(m.group(2))))
    return items


def count_local(year):
    web = os.path.join(OUT_ROOT, year, "web")
    thumbs = os.path.join(OUT_ROOT, year, "thumbnails")
    n_web = len([f for f in os.listdir(web) if f.endswith(".jpg")]) if os.path.isdir(web) else 0
    n_thumb = len([f for f in os.listdir(thumbs) if f.endswith("_thumb.jpg")]) if os.path.isdir(thumbs) else 0
    return n_web, n_thumb


def report(items):
    print("\nStan galerii (data/galeria.yml vs. static/galeria/):")
    for year, image_count in items:
        n_web, n_thumb = count_local(year)
        if n_web == 0 and n_thumb == 0:
            if image_count > 0:
                print(f"  {year}: brak lokalnie, image_count = {image_count} — zakładam, że pliki są na serwerze")
            else:
                print(f"  {year}: brak zdjęć, image_count = 0")
        elif n_web == n_thumb == image_count:
            print(f"  {year}: plików lokalnie = {n_web}, image_count = {image_count} ✓")
        else:
            print(f"  {year}: web = {n_web}, thumbnails = {n_thumb}, image_count = {image_count} ✗ UWAGA: liczby się różnią")
    print()


def image_hash(path):
    img = Image.open(path)
    img.draft("L", (256, 256))  # szybsze wczytanie dużych JPEG
    img = ImageOps.exif_transpose(img).convert("L").resize((HASH_SIZE, HASH_SIZE))
    px = list(img.getdata())
    avg = sum(px) / len(px)
    return [p > avg for p in px]


def hash_diff(a, b):
    return sum(x != y for x, y in zip(a, b))


def split_new(src, files, web_folder):
    """Dzieli oryginały na nowe i te, które już są w galerii (lista par: plik, numer w galerii)."""
    existing = {}
    for f in os.listdir(web_folder):
        m = re.fullmatch(r"(\d+)\.jpg", f)
        if m:
            existing[int(m.group(1))] = image_hash(os.path.join(web_folder, f))
    new, known = [], []
    for filename in files:
        try:
            h = image_hash(os.path.join(src, filename))
        except Exception:
            new.append(filename)  # nie-zdjęcie — pętla niżej je pominie z komunikatem
            continue
        num, diff = min(((n, hash_diff(h, eh)) for n, eh in existing.items()), key=lambda x: x[1])
        if diff <= SAME_PHOTO_MAX_DIFF:
            known.append((filename, num))
        else:
            new.append(filename)
    return new, known


def update_image_count(year, new_count):
    text = read_data()
    pattern = re.compile(
        r"(-\s*title\s*:\s*\"?" + re.escape(year) + r"\"?\s*\r?\n\s*image_count\s*:\s*)(\d+)"
    )
    m = pattern.search(text)
    if not m:
        print(f"UWAGA: w data/galeria.yml nie ma wpisu `title : {year}` w sekcji `item`.")
        print(f"       Dodaj go ręcznie z image_count : {new_count}.")
        return
    old_count = int(m.group(2))
    text = text[:m.start(2)] + str(new_count) + text[m.end(2):]
    with open(DATA_FILE, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(f"ZAKTUALIZOWANO data/galeria.yml: rok {year}, image_count {old_count} -> {new_count}")


def main():
    parser = argparse.ArgumentParser(description="Przygotowanie zdjęć do galerii PMCC")
    parser.add_argument("rok", nargs="?", help="rok edycji, np. 2025")
    args = parser.parse_args()

    print("Przygotowanie zdjęć do galerii PMCC")
    items = gallery_items(read_data())
    report(items)

    year = args.rok or ask("Który rok przetwarzamy? (np. 2025): ")
    if not re.fullmatch(r"\d{4}", year or ""):
        print(f"Błędny rok: '{year}'. Podaj 4 cyfry, np. 2025.")
        sys.exit(1)

    src = os.path.join(SRC_ROOT, year)
    if not os.path.isdir(src):
        print(f"Brak folderu z oryginałami: tmp/galeria/{year}/")
        print("Wrzuć tam zdjęcia i uruchom skrypt ponownie.")
        sys.exit(1)

    files = [f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f))]
    if not files:
        print(f"Folder tmp/galeria/{year}/ jest pusty.")
        sys.exit(1)
    print(f"Oryginały: tmp/galeria/{year}/ — {len(files)} plików")
    if not HEIF_OK:
        print("UWAGA: brak modułu pillow_heif — pliki HEIC/HEIF zostaną pominięte (pip install pillow-heif)")

    out = os.path.join(OUT_ROOT, year)
    thumb_folder = os.path.join(out, "thumbnails")
    web_folder = os.path.join(out, "web")
    n_web, n_thumb = count_local(year)
    start = 1
    if n_web or n_thumb:
        print(f"Folder static/galeria/{year}/ ma już zdjęcia (web = {n_web}, thumbnails = {n_thumb}).")
        print("  [n] nadpisz wszystko — cały rok od nowa, nowa kolejność (wgrać cały folder roku)")
        print("  [d] dopisz nowe     — stare bez zmian, nowe na końcu (wgrać tylko nowe pliki)")
        print("  [p] przerwij        — nic nie zmienia")
        choice = ask("Wybór [n/d/P]: ").lower()
        if choice in ("n", "nadpisz"):
            # czyścimy, żeby nie zostały stare pliki o wyższych numerach
            shutil.rmtree(thumb_folder, ignore_errors=True)
            shutil.rmtree(web_folder, ignore_errors=True)
        elif choice in ("d", "dopisz"):
            if n_web != n_thumb:
                print("Liczba plików web/ i thumbnails/ się różni — najpierw to wyjaśnij. Nic nie zmieniono.")
                sys.exit(1)
            print("Porównuję oryginały ze zdjęciami w galerii…")
            files, known = split_new(src, files, web_folder)
            print(f"Już w galerii (pomijam): {len(known)}")
            if not files:
                print("Brak nowych zdjęć. Nic nie zmieniono.")
                sys.exit(0)
            print(f"Nowe zdjęcia: {len(files)} — dostaną numery od {n_web + 1}")
            start = n_web + 1
        else:
            print("Przerwano, nic nie zmieniono.")
            sys.exit(0)

    os.makedirs(thumb_folder, exist_ok=True)
    os.makedirs(web_folder, exist_ok=True)

    # losowa kolejność — rozbija serie podobnych zdjęć
    random.shuffle(files)

    index = start
    for filename in files:
        try:
            img = Image.open(os.path.join(src, filename))
            img = ImageOps.exif_transpose(img)  # obrót wg EXIF
            if img.mode != "RGB":
                img = img.convert("RGB")

            thumb_img = img.copy()
            thumb_img.thumbnail(THUMB_SIZE)
            thumb_img.save(os.path.join(thumb_folder, f"{index}_thumb.jpg"), "JPEG", quality=JPEG_QUALITY)

            web_img = img.copy()
            web_img.thumbnail(WEB_SIZE)
            web_img.save(os.path.join(web_folder, f"{index}.jpg"), "JPEG", quality=JPEG_QUALITY)

            print(f"  {filename} -> {index}")
            index += 1
        except UnidentifiedImageError:
            print(f"  POMINIĘTO {filename}: to nie jest plik zdjęcia")
        except Exception as e:
            print(f"  POMINIĘTO {filename}: {e}")

    count = index - 1
    print(f"\nGotowe: static/galeria/{year}/, liczba zdjęć = {count}")
    if start > 1 and count >= start:
        print(f"Nowe pliki do wgrania: web/{start}.jpg … web/{count}.jpg oraz thumbnails/{start}_thumb.jpg … thumbnails/{count}_thumb.jpg")
    update_image_count(year, count)

    report(gallery_items(read_data()))
    if start > 1:
        print(f"Następny krok: wgraj przez FTP tylko nowe pliki (wyżej) do galeria/{year}/web/ i galeria/{year}/thumbnails/, potem `hugo` i public/ (zmienił się image_count).")
    else:
        print(f"Następny krok: wgraj przez FTP static/galeria/{year}/ (albo po `hugo` public/galeria/{year}/) na serwer do galeria/{year}/.")


if __name__ == "__main__":
    main()
