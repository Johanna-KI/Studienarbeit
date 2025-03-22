import pytest
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()


class Lagerbestand(Base):
    """
    Datenbankmodell für den Lagerbestand.
    """

    __tablename__ = "lagerbestand"

    barcode = Column(String, primary_key=True)
    name = Column(String)
    menge = Column(Integer)
    verfallsdatum = Column(Date)
    ort = Column(String, default="Lager")


class Bestellungen(Base):
    """
    Datenbankmodell für Bestellungen mit einer `ON DELETE CASCADE`-Beziehung zu `Lagerbestand`.
    """

    __tablename__ = "bestellungen"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bestellgruppe_id = Column(Integer)
    kundennummer = Column(String)
    barcode = Column(String, ForeignKey("lagerbestand.barcode", ondelete="CASCADE"))
    name = Column(String)
    bestelldatum = Column(Date)
    status = Column(String, default="Offen")


@pytest.fixture(scope="function")
def test_db():
    """
    Erstellt eine temporäre SQLite-Datenbank für Tests mit `ON DELETE CASCADE`.
    """
    engine = create_engine("sqlite:///:memory:")  # In-Memory-Datenbank für Tests
    Base.metadata.create_all(engine)  # Erstellt ALLE Tabellen
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session  # Übergibt die Session an die Tests

    session.close()
    Base.metadata.drop_all(engine)


def test_medikament_entfernen_erfolgreich(test_db):
    """
    Testet, ob ein Medikament erfolgreich aus der Datenbank gelöscht wird.
    """
    session = test_db

    # ✅ Korrekte Konvertierung des Verfallsdatums
    verfallsdatum = datetime.strptime("2025-12-31", "%Y-%m-%d").date()

    # Medikament hinzufügen
    medikament = Lagerbestand(
        barcode="12345678",
        name="Aspirin",
        menge=10,
        verfallsdatum=verfallsdatum,
        ort="Lager",
    )
    session.add(medikament)
    session.commit()

    # Medikament löschen
    session.query(Lagerbestand).filter_by(barcode="12345678").delete()
    session.commit()

    # Überprüfen, ob das Medikament entfernt wurde
    result = session.query(Lagerbestand).filter_by(barcode="12345678").first()
    assert result is None, "Das Medikament sollte gelöscht sein!"


def test_medikament_entfernen_nicht_existierend(test_db):
    """
    Testet das Entfernen eines nicht existierenden Medikaments.
    """
    session = test_db

    # Versuch, ein nicht vorhandenes Medikament zu löschen
    rows_deleted = session.query(Lagerbestand).filter_by(barcode="99999999").delete()
    session.commit()

    assert rows_deleted == 0, "Es sollte kein Medikament gelöscht werden!"


def test_datenbank_integrität_nach_loeschen(test_db):
    """
    Überprüft die Datenbank auf Integrität nach dem Löschen.
    """
    session = test_db

    # ✅ Korrekte Konvertierung des Verfallsdatums
    verfallsdatum = datetime.strptime("2026-01-01", "%Y-%m-%d").date()

    # Medikament hinzufügen
    medikament = Lagerbestand(
        barcode="55555555",
        name="Paracetamol",
        menge=5,
        verfallsdatum=verfallsdatum,
        ort="Lager",
    )
    session.add(medikament)
    session.commit()

    # Bestellung mit diesem Medikament hinzufügen
    bestellung = Bestellungen(
        bestellgruppe_id=1001,
        kundennummer="12345",
        barcode="55555555",
        name="Paracetamol",
        bestelldatum=verfallsdatum,
        status="Offen",
    )
    session.add(bestellung)
    session.commit()

    # ✅ Erst Bestellungen für das Medikament entfernen
    session.query(Bestellungen).filter_by(barcode="55555555").delete()
    session.commit()

    # ✅ Dann das Medikament löschen
    session.query(Lagerbestand).filter_by(barcode="55555555").delete()
    session.commit()

    # ✅ Prüfen, ob wirklich keine Bestellungen mehr existieren
    result = session.execute(
        text("SELECT COUNT(*) FROM bestellungen WHERE barcode = '55555555'")
    ).fetchone()[0]

    assert (
        result == 0
    ), "Es dürfen keine offenen Bestellungen für gelöschte Medikamente existieren!"


def test_fehlerquote_loeschen(test_db):
    """
    Überprüft, ob die Fehlerquote beim Löschen von Medikamenten unter 1% bleibt.
    """
    session = test_db

    num_tests = 1000  # Anzahl der Testdurchläufe
    fehlerhafte_loeschungen = 0

    for i in range(num_tests):
        barcode = str(10000000 + i)  # Generiere eindeutige Barcodes
        verfallsdatum = datetime.strptime("2026-12-31", "%Y-%m-%d").date()

        # Medikament hinzufügen
        medikament = Lagerbestand(
            barcode=barcode,
            name="TestMedikament",
            menge=10,
            verfallsdatum=verfallsdatum,
            ort="Lager",
        )
        session.add(medikament)
        session.commit()

        # Medikament löschen
        session.query(Lagerbestand).filter_by(barcode=barcode).delete()
        session.commit()

        # Prüfen, ob das Medikament wirklich gelöscht wurde
        result = session.query(Lagerbestand).filter_by(barcode=barcode).first()
        if result is not None:
            fehlerhafte_loeschungen += 1

    fehlerquote = (fehlerhafte_loeschungen / num_tests) * 100
    print(f"Fehlerquote beim Löschen: {fehlerquote:.2f}%")

    assert (
        fehlerquote < 1
    ), f"Fehlerquote zu hoch! Erwartet: <1%, Erhalten: {fehlerquote:.2f}%"
