import tempfile
import unittest
from datetime import date
from pathlib import Path
from app import create_app, connect


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)/'test.db'
        self.app = create_app(self.path, demo=False)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.client.get('/')
        with self.client.session_transaction() as session:
            self.csrf=session['csrf']
        self.data=dict(title='Python internship',organization='Test organization',kind='Internship',
                       location='Remote',deadline=date.today().isoformat(),benefit='Paid',url='https://example.org',
                       eligibility='Python',notes='My plan',csrf=self.csrf)

    def tearDown(self):
        self.temp.cleanup()

    def create(self):
        response=self.client.post('/new',data=self.data)
        self.assertEqual(response.status_code,302)
        return int(response.location.rsplit('/',1)[1])

    def post(self,item,action,**fields):
        return self.client.post(f'/opportunity/{item}/{action}',data={'csrf':self.csrf,**fields},follow_redirects=True)

    def test_create_and_checklist(self):
        item=self.create()
        response=self.client.get(f'/opportunity/{item}')
        self.assertIn(b'Python internship',response.data)
        self.assertIn(b'0 of 3 complete',response.data)
        with connect(self.path) as db:
            task=db.execute('SELECT id FROM tasks WHERE opportunity_id=?',(item,)).fetchone()[0]
        self.assertIn(b'1 of 3 complete',self.post(item,'toggle',task_id=task).data)
        self.assertIn(b'0 of 3 complete',self.post(item,'toggle',task_id=task).data)
        self.assertIn(b'Order transcript',self.post(item,'task',title='Order transcript').data)

    def test_edit_and_notes_persist(self):
        item=self.create()
        response=self.client.post(f'/opportunity/{item}/edit',data={**self.data,'title':'Updated title'},follow_redirects=True)
        self.assertIn(b'Updated title',response.data)
        self.post(item,'notes',notes='New plan')
        with connect(self.path) as db:
            self.assertEqual(db.execute('SELECT notes FROM opportunities WHERE id=?',(item,)).fetchone()[0],'New plan')
        create_app(self.path,demo=True)
        self.assertIn(b'Updated title',self.client.get('/').data)

    def test_stage_and_result(self):
        item=self.create()
        self.post(item,'stage',stage='Result',outcome='Accepted')
        self.assertIn(b'Accepted',self.client.get('/').data)
        self.post(item,'stage',stage='Preparing',outcome='Accepted')
        with connect(self.path) as db:
            row=db.execute('SELECT stage,outcome FROM opportunities').fetchone()
            self.assertEqual(tuple(row),('Preparing','Pending'))

    def test_archive_and_restore(self):
        item=self.create()
        self.post(item,'archive')
        self.assertNotIn(b'Python internship',self.client.get('/').data)
        self.assertIn(b'Python internship',self.client.get('/?view=archive').data)
        self.post(item,'archive')
        self.assertIn(b'Python internship',self.client.get('/').data)

    def test_search_type_stage_and_deadlines(self):
        item=self.create()
        self.assertIn(b'Python internship',self.client.get('/?q=remote').data)
        self.assertNotIn(b'<h3>Python internship</h3>',self.client.get('/?kind=Scholarship').data)
        self.assertNotIn(b'<h3>Python internship</h3>',self.client.get('/?stage=Submitted').data)
        self.assertIn(b'Due today',self.client.get('/?view=deadlines').data)
        self.post(item,'stage',stage='Submitted')
        self.assertNotIn(b'Python internship',self.client.get('/?view=deadlines').data)

    def test_validation_preserves_input(self):
        for field,value in [('deadline','bad'),('title',''),('kind','Other'),('url','javascript:alert(1)')]:
            with self.subTest(field=field):
                response=self.client.post('/new',data={**self.data,field:value})
                self.assertEqual(response.status_code,400)
                self.assertIn(b'Test organization',response.data)
        with connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM opportunities').fetchone()[0],0)

    def test_csrf_and_cross_opportunity_task_protection(self):
        self.assertEqual(self.client.post('/new',data={**self.data,'csrf':''}).status_code,400)
        first=self.create()
        second=self.create()
        with connect(self.path) as db:
            task=db.execute('SELECT id FROM tasks WHERE opportunity_id=?',(first,)).fetchone()[0]
        self.assertEqual(self.post(second,'toggle',task_id=task).status_code,404)

    def test_notes_escape_html(self):
        item=self.create()
        response=self.post(item,'notes',notes='<script>alert(1)</script>')
        self.assertNotIn(b'<script>alert(1)</script>',response.data)
        self.assertIn(b'&lt;script&gt;',response.data)

    def test_empty_and_missing_pages(self):
        self.assertIn(b'A fresh page',self.client.get('/').data)
        self.assertEqual(self.client.get('/new').status_code,200)
        self.assertEqual(self.client.get('/opportunity/999').status_code,404)

    def test_demo_pages_and_no_reseed(self):
        path=Path(self.temp.name)/'demo.db'
        client=create_app(path).test_client()
        self.assertIn(b'fictional practice data',client.get('/').data)
        self.assertIn(b'Future Leaders Fellowship',client.get('/opportunity/1').data)
        create_app(path)
        with connect(path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM opportunities').fetchone()[0],6)


if __name__=='__main__':
    unittest.main()
