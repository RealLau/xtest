import datetime
from haystack import indexes
from xtests.models import TestCase


class NoteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    last_update_time = indexes.DateTimeField(model_attr='last_update_time')

    def get_model(self):
        return TestCase

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(last_update_time__lte=datetime.datetime.now())