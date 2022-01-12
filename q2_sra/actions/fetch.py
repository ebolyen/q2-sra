#   Copyright 2021 Evan Bolyen
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import qiime2

import pandas as pd


from q2_sra.lib.efetch import runs_to_df, bioproject_to_df, DEFAULT_BATCH
from q2_sra.lib.munging import find_sra_col



def fetch_bioproject(bioproject: str, type: str,
                     batch_size: int=DEFAULT_BATCH) -> (pd.DataFrame, pd.DataFrame):
    print("Checking for BioProject and run files on SRA")
    collected_df = bioproject_to_df(bioproject, batch_size=batch_size,
                                    print_stdout=True)
    print("All accessions appear to exist.")

    return collected_df


def fetch_runs(accessions: qiime2.Metadata, type:str, where: str=None,
               col: str=None, skip_missing: bool=False,
               batch_size: int=DEFAULT_BATCH) -> (pd.DataFrame, pd.DataFrame):
    if where is not None:
        accessions = accessions.filter_ids(accessions.get_ids(where))
    # col: str, will be a column that exists and contains only SRR-vals 
    # or missing after re-assignment
    col = find_sra_col(accessions, col=col)
    column = accessions.get_column(col)
    if skip_missing:
        column = column.drop_missing_values()

    if column.has_missing_values():
        raise ValueError("Not all samples have an associated SRA-run accession"
                         " in column %r. Correct this manually, or use"
                         " `skip_missing` to ignore them." % col)

    # series is now a valid lookup
    series = column.to_series()
    print("SRA-run accessions collected. Checking for existence on SRA.")

    collected_df = runs_to_df(series, batch_size=batch_size, print_stdout=True)

    print("All accessions appear to exist.")


    return collected_df


def _download_from_df(collected_df):
    pass

