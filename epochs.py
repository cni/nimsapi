# @author:  Gunnar Schaefer

import json
import webapp2
import bson.json_util

import nimsapiutil


class Epochs(nimsapiutil.NIMSRequestHandler):

    def count(self, iid):
        """Return the number of Epochs."""
        self.response.write('epochs count\n')

    def post(self, iid):
        """Create a new Epoch."""
        self.response.write('epochs post\n')

    def get(self, iid, sid):
        """Return the list of Session Epochs."""
        session = self.app.db.sessions.find_one({'_id': bson.objectid.ObjectId(sid)})
        if not session:
            self.abort(404)
        experiment = self.app.db.experiments.find_one({'_id': bson.objectid.ObjectId(session['experiment'])})
        if not experiment:
            self.abort(500)
        if not self.user_is_superuser and self.userid not in experiment['permissions']:
            self.abort(403)
        query = {'session': bson.objectid.ObjectId(sid)}
        projection = ['timestamp', 'series', 'acquisition', 'description', 'datatype']
        epochs = list(self.app.db.epochs.find(query, projection))
        self.response.write(json.dumps(epochs, default=bson.json_util.default))

    def put(self, iid):
        """Update many Epochs."""
        self.response.write('epochs put\n')


class Epoch(nimsapiutil.NIMSRequestHandler):

    def get(self, iid, eid):
        """Return one Epoch, conditionally with details."""
        epoch = self.app.db.epochs.find_one({'_id': bson.objectid.ObjectId(eid)})
        if not epoch:
            self.abort(404)
        session = self.app.db.sessions.find_one({'_id': epoch['session']})
        if not session:
            self.abort(500)
        experiment = self.app.db.experiments.find_one({'_id': bson.objectid.ObjectId(session['experiment'])})
        if not experiment:
            self.abort(500)
        if not self.user_is_superuser and self.userid not in experiment['permissions']:
            self.abort(403)
        self.response.write(json.dumps(epoch, default=bson.json_util.default))

    def put(self, iid, eid):
        """Update an existing Epoch."""
        self.response.write('epoch %s put, %s\n' % (epoch_id, self.request.params))

    def delete(self, iid, eid):
        """Delete an Epoch."""
        self.response.write('epoch %s delete, %s\n' % (epoch_id, self.request.params))
