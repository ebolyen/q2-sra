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

import os

from q2_types.sample_data import SampleData

import qiime2
import qiime2.plugin.model as model
from qiime2.plugin import SemanticType


SRAMetadata = SemanticType('SRAMetadata', variant_of=SampleData.field['type'])


class MetadataFormat(model.TextFileFormat):
    def validate(self, *args):
        try:
            md = qiime2.Metadata.load(str(self))
        except qiime2.metadata.MetadataFileError as md_exc:
            raise ValidationError(md_exc) from md_exc


MetadataDirFmt = model.SingleFileDirectoryFormat(
    'MetadataDirFmt', 'metadata.tsv', MetadataFormat)
