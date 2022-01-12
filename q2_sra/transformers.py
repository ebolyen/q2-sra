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


import pandas as pd
import qiime2

from q2_sra.plugin_setup import plugin
from q2_sra.format_types import MetadataFormat


@plugin.register_transformer
def from_md(data: qiime2.Metadata) -> MetadataFormat:
    ff = MetadataFormat()
    data.save(str(ff))
    return ff


@plugin.register_transformer
def to_md(ff: MetadataFormat) -> qiime2.Metadata:
    return qiime2.Metadata.load(str(ff))


@plugin.register_transformer
def _1(data: pd.DataFrame) -> MetadataFormat:
    return from_md(qiime2.Metadata(data))


@plugin.register_transformer
def _1(ff: MetadataFormat) -> pd.DataFrame:
    return to_md(ff).to_dataframe()

