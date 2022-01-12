import xml.etree.ElementTree as et
import re
import itertools
import math
import sys

import requests
import pandas as pd


DEFAULT_BATCH = 250


def bioproject_to_df(bioproject, batch_size=DEFAULT_BATCH, print_stdout=False):
    return _fetch_to_df(
        bioproject_fetch(bioproject, batch_size=batch_size,
                         print_stdout=print_stdout)
    )


def runs_to_df(ids: pd.Series, batch_size=DEFAULT_BATCH, print_stdout=False):
    return _fetch_to_df(
        runs_fetch(ids, batch_size=batch_size, print_stdout=print_stdout)
    )


def _fetch_to_df(source):
    records = [collate_experiment(exp) for exp in source]
    df = pd.json_normalize(records).set_index('id')
    return df


def bioproject_fetch(bioproject, batch_size=DEFAULT_BATCH, print_stdout=False):
    if not bioproject.startswith('PRJNA'):
        raise ValueError("%r is not a BioProject id (should start with PRJNA)"
                         % bioproject)

    uid = bioproject[len('PRJNA'):]
    # URL hacked from thin air by guessing that the website's query params
    # would work in e-utils.
    resp = requests.post("https://eutils.ncbi.nlm.nih.gov"
                         "/entrez/eutils/elink.fcgi",
                         data={'linkname': 'bioproject_sra',
                               'from_uid': uid})
    if not resp.ok:
        raise ValueError()

    elem = et.fromstring(resp.content)
    ids = pd.Series((l.text for l in elem.findall('.//Link/Id')))

    yield from runs_fetch(ids, batch_size=batch_size,
                          print_stdout=print_stdout, check_ids=False)
                          # IDs of links are not SRR IDs or even
                          # present in the XML


def runs_fetch(ids: pd.Series, batch_size=DEFAULT_BATCH, print_stdout=False,
               check_ids=True):
    n_batches = None
    if len(ids) > batch_size:
        n_batches = math.ceil(len(ids) / batch_size)
    for num, ((start, end), batch) in enumerate(chunker(ids, batch_size), 1):
        found = set()
        if n_batches is not None and print_stdout:
            print("Checking ids %d..%d out of %d (batch %d/%d)"
                  % (start+1, end, len(ids), num, n_batches))

        for exp in raw_efetch(*batch, retmax=batch_size):
            found.add(get_id(exp))
            yield exp

        if check_ids:
            found = batch.isin(found)
            if not found.all():
                LIM = 10
                missing = batch[~found]
                message = ', '.join(missing[:LIM])
                if len(missing) > LIM:
                    message += ', ... (and %d others) ...' % (
                            len(missing) - LIM)
                if n_batches is not None:
                    message += ' (in batch %d/%d)' % (num, n_batches)
                raise ValueError(
                    "The following accessions could not be found: " + message)
        else:
            if len(found) != len(batch):
                raise ValueError("Lost %d accessions from NCBI timeout."
                                 % (len(batch) - len(found)))


def chunker(seq, size):
    # SO: https://stackoverflow.com/a/434328/579416
    for pos in range(0, len(seq), size):
        chunk = seq[pos:pos+size]
        yield (pos, pos + len(chunk)), chunk


def raw_efetch(*ids, db='sra', retmax=150):
    msg = None
    resp = requests.post("https://eutils.ncbi.nlm.nih.gov"
                         "/entrez/eutils/efetch.fcgi",
                         data={"db": db, "retmax": retmax,
                               "id": ','.join(ids)},
                         stream=True)
    resp.raw.decode_content = True
    for _, elem in et.iterparse(resp.raw, events=['end']):
        if elem.tag == "EXPERIMENT_PACKAGE":
            yield elem
        elif elem.tag == "ERROR":
            msg = elem.text
            break

    if msg is not None or not resp.ok:
        raise ValueError('eutils error: ' + msg)


def get_id(experiment):
    return experiment.find('.//RUN/IDENTIFIERS/PRIMARY_ID').text


def collate_experiment(experiment):
    desc = {}
    desc['id'] = get_id(experiment)
    desc['alias'] =  experiment.find('.//SAMPLE').attrib.get('alias')

    desc['layout'] = experiment.find('.//DESIGN//LIBRARY_LAYOUT/*').tag.lower()

    stats = experiment.find(".//RUN//Statistics")
    if stats is not None:
        desc['nreads'] = int(stats.attrib.get('nreads'))
        # Handle "reads" with no spots.
        count = 0
        for read in stats.findall("./Read"):
            c = int(read.attrib.get('count', 0))
            if c > 0:
                count += 1
        if count > 0:
            desc['nreads'] = count
    else:
        desc['nreads'] = None

    desc['original_files'] = \
        ':'.join(f.attrib.get("filename") for f in
                 experiment.findall(".//RUN//SRAFile[@supertype='Original']"))

    desc['bioproject_number'] = experiment.find(
            ".//EXTERNAL_ID[@namespace='BioProject']").text
    desc['biosample_number'] = experiment.find(
            ".//EXTERNAL_ID[@namespace='BioSample']").text

    desc['description'] = ': '.join((
        experiment.find('.//EXPERIMENT/TITLE').text,
        experiment.find('.//EXPERIMENT//DESIGN_DESCRIPTION').text
    ))

    for elem in experiment.findall(".//EXPERIMENT//LIBRARY_DESCRIPTOR/*"):
        if elem.text is None:
            continue
        desc[elem.tag.lower()] = elem.text

    for key, val in zip(
            experiment.findall(".//SAMPLE//SAMPLE_ATTRIBUTES//TAG"),
            experiment.findall(".//SAMPLE/SAMPLE_ATTRIBUTES//VALUE")):
        if val.text.lower() in {'na', 'not collected', 'n/a'}:
            continue
        desc[pretty_header(key.text)] = val.text


    return desc


def pretty_header(some_damn_header):
    # from SO: https://stackoverflow.com/a/9283563/579416
    return re.sub(
        r"""
        (            # start the group
            # alternative 1
        (?<=[a-z])  # current position is preceded by a lower char
                    # (positive lookbehind: does not consume any char)
        [A-Z]       # an upper char
                    #
        |   # or
            # alternative 2
        (?<!\A)     # current position is not at the beginning of the str
                    # (negative lookbehind: does not consume any char)
        [A-Z]       # an upper char
        (?=[a-z])   # matches if next char is a lower char
                    # lookahead assertion: does not consume any char
        )           # end the group
        """, r'_\1', some_damn_header, flags=re.VERBOSE).lower()
