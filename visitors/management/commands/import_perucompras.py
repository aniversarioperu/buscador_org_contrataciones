from datetime import datetime
import csv
from unidecode import unidecode
import hashlib

from django.core.management.base import BaseCommand
from visitors.models import Visitor


class Command(BaseCommand):
    help = 'imports records from perucompras.gob.pe from CSV files ' \
           'headers:' \
           '- nombre_visita' \
           '- fecha_inicio' \
           '- fecha_fin' \
           '- documento' \
           '- empresa' \
           '- area' \
           '- motivo' \
           '- contacto' \
           '- cargo_contacto' \
           '- dni'

    def add_arguments(self, parser):
        parser.add_argument("filename")

    def handle(self, *args, **options):
        do_import(options["filename"])


def do_import(filename):
    visitors = []
    hashes = []
    with open(filename, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            date_str = get_visit_date_str(row)
            time_start = get_time_start(row)
            time_end = get_time_end(row)
            id_document = get_id_document(row)

            item = {
                "institution": "perucompras",
                "full_name": row["nombre_visita"],
                "id_document": "dni",
                "id_number": row["documento"],
                "date": date_str,
                "time_start": time_start,
                "time_end": time_end,
            }
            item = make_hash(item)
            hash_str = item["sha1"]
            if hash_str in hashes:
                continue
            queryset = Visitor.objects.filter(sha1=hash_str)
            if not queryset:
                host_title = row.get("cargo_contacto", "")
                hashes.append(hash_str)
                visitors.append(
                    Visitor(
                        date=date_str,
                        institution="perucompras",
                        sha1=hash_str,
                        full_name=item["full_name"],
                        entity=row["empresa"],
                        office=row["area"],
                        id_document=id_document,
                        id_number=item["id_number"],
                        reason=row["motivo"],
                        host_name=row["contacto"],
                        time_start=time_start,
                        time_end=time_end,
                        host_title=host_title,
                    )
                )
    Visitor.objects.bulk_create(visitors)
    print("creating {} visitors".format(len(visitors)))


def get_id_document(row):
    try:
        id_document = row["id_document"]
    except KeyError:
        id_document = "dni"
    return id_document


def get_time_start(row):
    try:
        time_start = get_time(row["fecha_inicio"])
    except KeyError:
        time_start = get_time(row["hora_inicio"])
    return time_start


def get_time_end(row):
    try:
        time_end = get_time(row["fecha_fin"])
    except KeyError:
        time_end = get_time(row["hora_fin"])
    return time_end


def get_visit_date_str(row):
    try:
        date_str = get_visit_date(row["fecha_inicio"])
    except KeyError:
        date_str = get_visit_date(row["fecha"])
    return date_str


def get_visit_date(fecha_inicio):
    """

    :param fecha_inicio:
    :return: date string YYYY-mm-dd
    """
    if not fecha_inicio.strip():
        return ""
    try:
        date_obj = datetime.strptime(fecha_inicio, "%m/%d/%y %H:%M %p")
    except ValueError:
        try:
            date_obj = datetime.strptime(fecha_inicio, "%m/%d/%y %H:%M")
        except ValueError:
            try:
                date_obj = datetime.strptime(fecha_inicio, "%m/%d/%Y %H:%M")
            except ValueError:
                try:
                    date_obj = datetime.strptime(fecha_inicio, "%m/%d/%Y")
                except ValueError:
                    date_obj = datetime.strptime(fecha_inicio, "%d/%m/%Y %H:%M")
    return date_obj.strftime("%Y-%m-%d")


def get_time(fecha):
    if not fecha.strip():
        return ""
    if fecha.lower() == "no iniciado":
        return ""
    try:
        date_obj = datetime.strptime(fecha, "%m/%d/%y %H:%M %p")
    except ValueError:
        try:
            date_obj = datetime.strptime(fecha, "%m/%d/%y %H:%M")
        except ValueError:
            try:
                date_obj = datetime.strptime(fecha, "%m/%d/%Y %H:%M")
            except ValueError:
                try:
                    date_obj = datetime.strptime(fecha, "%H:%M:%S %p")
                except ValueError:
                    date_obj = datetime.strptime(fecha, "%d/%m/%Y %H:%M")
    return date_obj.strftime("%H:%M")


def make_hash(item):
    hash_input = ''
    hash_input += str(item['institution'])

    if 'full_name' in item:
        hash_input += str(unidecode(item['full_name']))

    if 'id_document' in item:
        hash_input += str(unidecode(item['id_document']))

    if 'id_number' in item:
        hash_input += str(unidecode(item['id_number']))

    hash_input += str(item['date'])

    if 'time_start' in item:
        hash_input += str(unidecode(item['time_start']))

    hash_output = hashlib.sha1()
    hash_output.update(hash_input.encode("utf-8"))
    item['sha1'] = hash_output.hexdigest()
    return item
