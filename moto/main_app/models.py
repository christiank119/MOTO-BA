from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
from main_app.models import CGroup
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db.models import Q


# Create your models here.

# Zeitraum enthält zwei Uhrzeiten
class Timespan(models.Model):
    starttime = models.TimeField()
    endtime = models.TimeField(null=True)
# Datumsraum enhält zwei Tage mit konkreter Uhrzeit
class Datespan(models.Model):
    startdate = models.DateTimeField()
    enddate = models.DateTimeField()
class Custom_user(models.Model):
    first_name = models.CharField(max_length=100)
    second_name = models.CharField(max_length=100)
    tag_id = models.CharField(max_length=100, null=True)          #max_length abhängig von Tags id länge
    # email = models.CharField(max_length=100)
class Pedagogical_specialist(models.Model):
    role = models.CharField(max_length=40)
    #rigths = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)       # null=True rausmachen
    custom_user = models.ForeignKey(Custom_user, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null= True)    # null=True rausmachen
    is_password_otp = models.BooleanField(default=True)

    def get_accessible_students(self):
        
        groups = CGroup.objects.filter(Q(supervisor=self) | Q(representative=self))
    
        combined_groups = CombinedGroup.objects.filter(pedagogical_specialists=self)
        combined_group_ids = combined_groups.values_list('groups', flat=True)

        all_group_ids = set(groups.values_list('id', flat=True)) | set(combined_group_ids)
    
        students = Student.objects.filter(group_id__in=all_group_ids).distinct()
        
        return students
    
    @classmethod
    def get_free_and_occupied(cls):
        pssfree = []
        pssoccupied = []
        for pa in cls.objects.all():
            if Group.objects.filter(gruppen_leiter=pa).exists():
                pssoccupied.append(pa)
            else:
                pssfree.append(pa)
        return pssfree, pssoccupied
    
    @classmethod
    def get_by_id(cls, id):
        """
        Liefert das Pedagogical_specialist-Objekt, das der übergebenen ID entspricht.
        Wenn id_value keine gültige ID darstellt, wird None zurückgegeben.
        Existiert das Objekt nicht, gibt die Methode 0 zurück.
        """
        try:
            # Versuch, id_value in einen Integer umzuwandeln
            _id = int(id)
        except (ValueError, TypeError):
            return None
        try:
            obj = cls.objects.get(id=_id)
            return obj
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_ps_by_custom_user_id(cls, id):
        try:
            _id = int(id)
        except (ValueError, TypeError):
            return None

        try:
            return cls.objects.get(custom_user__id=_id)
        except cls.DoesNotExist:
            return None

    class Meta:
        permissions = [("can_import", "Can import excel data")]

class Room(models.Model):
    room_name = models.CharField(max_length=15)
    building = models.CharField(max_length=15)
    floor = models.SmallIntegerField(null=True)   # Später null weg
    capacity = models.SmallIntegerField()
    category = models.CharField(max_length=30, null = True)
    color = models.CharField(max_length=7, default="#FFFFFF", help_text="Hex color code, e.g., #FFFFFF for white")

    def get_schueler_in_raum(self):
        visits = Visit.objects.filter(raum_id=self, zeitraum__endzeit__isnull=True)
        return [a.student for a in visits]

    @classmethod
    def get_free_and_occupied(cls):
        """
        Teilt alle Room-Instanzen in zwei Listen auf:
         - roomsfree: Räume, für die es kein zugehöriges Gruppe-Objekt gibt.
         - roomsoccupied: Räume, die in mindestens einem Gruppe-Objekt referenziert werden.
        """
        roomsfree = []
        roomsoccupied = []
        for room in cls.objects.all():
            if Group.objects.filter(raum=room).exists():
                roomsoccupied.append(room)
            else:
                roomsfree.append(room)
        return roomsfree, roomsoccupied
    
    @classmethod
    def get_by_id(cls, id):
        try:
            _id = int(id)
        except (ValueError, TypeError):
            return None
        try:
            obj = cls.objects.get(id=_id)
            return obj
        except cls.DoesNotExist:
            return None
#Wichtig hier noch model überarbeiten
class Group(models.Model):
    name = models.CharField(max_length=50)
    supervisor = models.ManyToManyField(Pedagogical_specialist)        # ? mehere Gruppenleiter?
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, related_name='leitende_gruppen')
    representative = models.ForeignKey(Pedagogical_specialist, on_delete=models.SET_NULL, null=True, related_name='vertretende_gruppen')

    @classmethod
    def get_by_id(cls, id):
        try:
            _id = int(id)
        except (ValueError, TypeError):
            return None
        try:
            return cls.objects.get(id=_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_by_name(cls, name):
        """
        Liefert das Group-Objekt, dessen Name dem übergebenen name_value entspricht.
        Falls name_value kein String ist oder None, wird None zurückgegeben.
        Existiert das Objekt nicht, gibt die Methode 0 zurück.
        """
        if not isinstance(name, str) or name is None:
            return None
        try:
            return cls.objects.get(name=name)
        except cls.DoeesNotExist:
            return None

class CombinedGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    groups = models.ManyToManyField(Group, related_name='combined_groups')
    pedagogical_specialists = models.ManyToManyField('Pedagogical_specialist', blank=True, related_name='combined_groups_access')

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        from main_app.models import Setting  # Import innerhalb der Methode, um zyklische Importe zu vermeiden

        # Holen der globalen Einstellung combine_groups_all_ps
        combine_all_ps_setting = Setting.objects.get(key='combine_groups_all_ps').value.lower() == 'true'

        if combine_all_ps_setting:
            # Wenn in den Settings combine_groups_all_ps=True ist -> Alle Gruppenleiter übernehmen
            all_supervisors = set()
            for group in self.groups.all():
                all_supervisors.update(group.supervisor.all())
            self.pedagogical_specialists.set(all_supervisors)

        else:
            # Falls False, prüfe die Optionen: Übergabe von Fachkräften, erste Gruppe oder spezielle Gruppe
            if not self.pedagogical_specialists.exists():
                if kwargs.get('specific_group'):
                    specific_group = kwargs['specific_group']
                    self.pedagogical_specialists.set(specific_group.supervisor.all())
                else:
                    first_group = self.groups.first()
                    if first_group:
                        self.pedagogical_specialists.set(first_group.supervisor.all())
                    else:
                        raise ValidationError("Es muss entweder eine Gruppe oder eine Liste von Fachkräften angegeben werden.")

        super().save(*args, **kwargs)

    def add_groups(self, new_groups, specific_group=None):
        from main_app.models import Setting

        combine_all_ps_setting = Setting.objects.get(key='combine_groups_all_ps').value.lower() == 'true'

        # Gruppen hinzufügen
        self.groups.add(*new_groups)

        if combine_all_ps_setting:
            # Wenn Setting True ist, alle Supervisoren der neuen Gruppen hinzufügen
            for group in new_groups:
                self.pedagogical_specialists.add(*group.supervisor.all())

        else:
            # Falls False, nimm Supervisoren von der angegebenen Gruppe oder von der ersten neuen Gruppe
            if specific_group:
                self.pedagogical_specialists.set(specific_group.supervisor.all())
            else:
                first_new_group = new_groups[0] if isinstance(new_groups, list) else new_groups.first()
                self.pedagogical_specialists.set(first_new_group.supervisor.all())

        self.save()

    def __str__(self):
        return f"Combined Group: {self.name}"

#class AGZeit(models.Model):
#    class WOCHENTAG(models.TextChoices):
#        MONTAG = "Montag"
#        DIENSTAG = "Dienstag"
#        MITTWOCH = "Mittwoch"
#        DONNERSTAG = "Donnerstag"
#        FREITAG = "Freitag"
    
#    wochentag = models.TextField(choices=WOCHENTAG.choices, default=WOCHENTAG.MONTAG, max_length=10)
#    zeitraum = models.ForeignKey(Timespan, on_delete=models.CASCADE)

class Ag_category(models.Model):
    name = models.CharField(max_length=100)

class Ag(models.Model):
    name = models.CharField(max_length=50)
    max_participant = models.SmallIntegerField()
#    offene_AG = models.BooleanField() 
    supervisor = models.ForeignKey(Pedagogical_specialist, on_delete=models.CASCADE, null=True)       # null=True entfernen
#    angebots_datum_raum = models.ForeignKey(Datumsraum, on_delete=models.CASCADE, null=True)    # null=True entfernen
#    ag_zeit = models.ManyToManyField(AGZeit)
    ag_category = models.ForeignKey(Ag_category, on_delete=models.CASCADE, null=True)
    timespan = models.ForeignKey(Timespan, on_delete=models.CASCADE, null = True)

class Student(models.Model):
    school_class = models.CharField(max_length=3)             # optional
    bus = models.BooleanField()
    name_lg = models.CharField(max_length=100)
    contact_lg = models.CharField(max_length=300)
    in_house = models.BooleanField(default=False)      # Ist kind überhaupt an diesem Tag in der OGS
    wc = models.BooleanField(default=False)
    school_yard = models.BooleanField(default=False)
    custom_user = models.ForeignKey(Custom_user, on_delete=models.SET_NULL, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
#    ag_buchungen = models.ManyToManyField(AG)

    @classmethod
    def get_student_by_custom_user_id(cls, id):
        try:
            _id = int(id)
        except (ValueError, TypeError):
            return None

        try:
            return cls.objects.get(custom_user__id=_id)
        except cls.DoesNotExist:
            return None

class Feedback(models.Model):
    class Feedbacks(models.TextChoices):
        GOOD = "GOOD", "Good"
        MEDIUM = "MEDIUM", "Medium"
        BAD = "BAD", "Bad"

    feedback_value = models.CharField(choices=Feedbacks.choices, default=Feedbacks.MEDIUM, max_length=6)
    day = models.DateField()
    time = models.TimeField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    mensa_feedback = models.BooleanField(default=False)
class Room_occupancy(models.Model):
    device_id = models.CharField(max_length=200,null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    ag = models.ForeignKey(Ag, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    timespan = models.ForeignKey(Timespan, on_delete=models.CASCADE)
    supervisor = models.ManyToManyField(Pedagogical_specialist)   # Wird hier wirklich einer Benötigt?
class Visit(models.Model):                # Zuordnung wo sich Kinder befunden haben, wird mit löschen des Zeitraums auch gelöscht
    day = models.DateField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    timespan = models.ForeignKey(Timespan, on_delete=models.CASCADE)
class Room_history(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    ag_name = models.CharField(max_length=50, null = True)
    day = models.DateField()
    timespan = models.ForeignKey(Timespan, on_delete=models.CASCADE)
    ag_category = models.ForeignKey(Ag_category, on_delete=models.CASCADE, null = True)
    supervisor = models.ForeignKey(Pedagogical_specialist, on_delete=models.CASCADE)
    max_participant = models.SmallIntegerField()
# class Buchung_AG(models.Model):            # Zuordunung zwischen Schüler und AGS
#     schueler_id = models.ForeignKey(Schueler, on_delete=models.CASCADE)
#     ag_id = models.ForeignKey(AG, on_delete=models.CASCADE)
    
class Setting(models.Model):
    CATEGORY_CHOICES = [
        ('always', 'Immer änderbar'),
        ('restart', 'Erfordert Neustart'),
        ('db_reset', 'Erfordert DB-Reset')
    ]
    
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='always')
    description = models.TextField(blank=True, null=True)
    requires_restart = models.BooleanField(default=False)
    requires_db_reset = models.BooleanField(default=False)

    def __str__(self):
        return self.key

@receiver(pre_delete, sender=Student)
def delete_related_user(sender, instance, **kwargs):
    if instance.user_id:
        user = instance.user_id
        instance.user_id = None  # Um eine Endlosschleife zu verhindern, setzen Sie das ForeignKey-Feld auf None
        user.delete()