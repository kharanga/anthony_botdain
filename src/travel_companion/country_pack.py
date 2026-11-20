from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, TypeVar
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, RootModel, StringConstraints, ValidationError

from travel_companion.cards import Evidence

PACK_MANIFEST_FILE = "pack.yaml"
ALLERGEN_TERMS_FILE = "allergen_terms.yaml"

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class InvalidCountryPack(Exception):
    pass


def known_time_zone(time_zone: str) -> str:
    try:
        ZoneInfo(time_zone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError(f"unknown time zone {time_zone!r}") from error
    return time_zone


class StrictPackModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class GuideReference(StrictPackModel):
    zim_file: NonEmptyText
    article: NonEmptyText


class PackManifest(StrictPackModel):
    country: NonEmptyText
    name: NonEmptyText
    language: NonEmptyText
    currencies: Annotated[list[CurrencyCode], Field(min_length=1)]
    time_zone: Annotated[str, AfterValidator(known_time_zone)]
    guide: GuideReference


class AllergenTermsFile(RootModel[dict[NonEmptyText, Annotated[list[NonEmptyText], Field(min_length=1)]]]):
    pass


@dataclass(frozen=True)
class AllergenTerm:
    allergen: str
    text: str
    source: Path


@dataclass(frozen=True)
class CountryPack:
    folder: Path
    manifest: PackManifest
    allergen_terms: tuple[AllergenTerm, ...]

    def terms_for(self, allergen: str) -> tuple[AllergenTerm, ...]:
        return tuple(term for term in self.allergen_terms if term.allergen == allergen)


PackFileModel = TypeVar("PackFileModel", bound=BaseModel)


def parsed_yaml(path: Path) -> object:
    if not path.is_file():
        raise InvalidCountryPack(f"Country Pack file {path} is missing")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise InvalidCountryPack(f"Country Pack file {path} is not valid YAML: {error}") from error


def validation_problems(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in problem['loc']) or 'top level'}: {problem['msg']}"
        for problem in error.errors()
    )


def validated_pack_file(path: Path, model: type[PackFileModel]) -> PackFileModel:
    try:
        return model.model_validate(parsed_yaml(path))
    except ValidationError as error:
        raise InvalidCountryPack(f"Country Pack file {path} is invalid: {validation_problems(error)}") from error


def loaded_manifest(pack_folder: Path, country: str) -> PackManifest:
    manifest_path = pack_folder / PACK_MANIFEST_FILE
    manifest = validated_pack_file(manifest_path, PackManifest)
    if manifest.country != country:
        raise InvalidCountryPack(
            f"Country Pack file {manifest_path} is invalid: country is {manifest.country!r}, expected {country!r}"
        )
    return manifest


def loaded_allergen_terms(pack_folder: Path, required_allergens: tuple[str, ...]) -> tuple[AllergenTerm, ...]:
    terms_path = pack_folder / ALLERGEN_TERMS_FILE
    terms_by_allergen = validated_pack_file(terms_path, AllergenTermsFile).root
    missing_allergens = [allergen for allergen in required_allergens if allergen not in terms_by_allergen]
    if missing_allergens:
        raise InvalidCountryPack(
            f"Country Pack file {terms_path} is invalid: no Allergen Terms for active Allergen {', '.join(missing_allergens)}"
        )
    return tuple(
        AllergenTerm(allergen=allergen, text=term_text, source=terms_path)
        for allergen, term_texts in terms_by_allergen.items()
        for term_text in term_texts
    )


def load_country_pack(packs_dir: Path, country: str, required_allergens: tuple[str, ...]) -> CountryPack:
    pack_folder = Path(packs_dir) / country
    if not pack_folder.is_dir():
        raise InvalidCountryPack(f"Country Pack folder {pack_folder} is missing")
    return CountryPack(
        folder=pack_folder,
        manifest=loaded_manifest(pack_folder, country),
        allergen_terms=loaded_allergen_terms(pack_folder, required_allergens),
    )


def country_pack_evidence(pack: CountryPack) -> list[Evidence]:
    manifest_source = str(pack.folder / PACK_MANIFEST_FILE)
    manifest = pack.manifest
    return [
        Evidence(source=manifest_source, text=f"currencies = {', '.join(manifest.currencies)}"),
        Evidence(source=manifest_source, text=f"time_zone = {manifest.time_zone}"),
        Evidence(source=manifest_source, text=f"guide = {manifest.guide.zim_file} ({manifest.guide.article})"),
    ]
