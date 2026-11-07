"""Suite de tests unitarios para pyindec."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock

import pandas as pd
import requests

import pyindec
from pyindec import (
    ENDPOINTS,
    SIGNOS_CONVENCIONALES,
    F,
    IndecAPIError,
    IndecAuthError,
    IndecClient,
    IndecFilterError,
    IndecNotFoundError,
    IndecPermissionError,
    IndecRateLimitError,
    describe_endpoint,
    explain_sign,
    list_endpoints,
    parse_content_range,
)


def _mock_response(
    data: list | dict,
    *,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
    url: str = "https://api.indec.gob.ar/v1/ipc_nacional",
) -> requests.Response:
    resp = requests.Response()
    resp.status_code = status_code
    resp.url = url
    resp._content = json.dumps(data).encode("utf-8")
    if headers:
        resp.headers.update(headers)
    return resp


class TestPyIndec(unittest.TestCase):
    def setUp(self) -> None:
        self.session = MagicMock(spec=requests.Session)
        self.client = IndecClient(token="test-jwt-token", session=self.session)

    def test_auth_missing_token_raises(self) -> None:
        client = IndecClient(token=None, session=self.session, load_dotenv=False)
        with self.assertRaises(IndecAuthError):
            client.ipc_nacional()

    def test_auth_bearer_prefix_stripped(self) -> None:
        client = IndecClient(token="Bearer my-secret-jwt", session=self.session)
        self.assertEqual(client.token, "my-secret-jwt")

    def test_all_postgrest_operators(self) -> None:
        self.assertEqual(F.eq(2024).to_postgrest(), "eq.2024")
        self.assertEqual(F.neq("inactivo").to_postgrest(), "neq.inactivo")
        self.assertEqual(F.gt(18).to_postgrest(), "gt.18")
        self.assertEqual(F.gte(18).to_postgrest(), "gte.18")
        self.assertEqual(F.lt(100).to_postgrest(), "lt.100")
        self.assertEqual(F.lte(100).to_postgrest(), "lte.100")
        self.assertEqual(F.like("*Juan*").to_postgrest(), "like.*Juan*")
        self.assertEqual(F.ilike("%juan%").to_postgrest(), "ilike.*juan*")
        self.assertEqual(F.contains("alimentos").to_postgrest(), "ilike.*alimentos*")
        self.assertEqual(F.startswith("GBA").to_postgrest(), "ilike.GBA*")
        self.assertEqual(F.endswith("total").to_postgrest(), "ilike.*total")
        self.assertEqual(F.in_(["GBA", "Pampeana"]).to_postgrest(), "in.(GBA,Pampeana)")
        self.assertEqual(F.is_(None).to_postgrest(), "is.null")
        self.assertEqual(F.is_null().to_postgrest(), "is.null")
        self.assertEqual(F.is_(True).to_postgrest(), "is.true")
        self.assertEqual(F.is_(False).to_postgrest(), "is.false")
        self.assertEqual(F.between(2022, 2024).to_postgrest_list(), ["gte.2022", "lte.2024"])

    def test_query_builder_params_and_execution(self) -> None:
        sample = [{"periodo": "202401", "region": "GBA", "valor": 20.6}]
        self.session.get.return_value = _mock_response(sample)

        df = (
            self.client.query("ipc")
            .select("periodo,region", "valor")
            .eq("region", "GBA")
            .between("anio", 2023, 2024)
            .ilike("descripcion", "*alimentos*")
            .is_("observaciones", None)
            .order("periodo", desc=True)
            .limit(50)
            .offset(10)
            .df()
        )

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["valor"], 20.6)

        call_args = self.session.get.call_args
        self.assertEqual(call_args[0][0], "https://api.indec.gob.ar/v1/ipc_nacional")
        params = call_args[1]["params"]
        self.assertEqual(
            params,
            [
                ("select", "periodo,region,valor"),
                ("order", "periodo.desc"),
                ("limit", "50"),
                ("offset", "10"),
                ("region", "eq.GBA"),
                ("anio", "gte.2023"),
                ("anio", "lte.2024"),
                ("descripcion", "ilike.*alimentos*"),
                ("observaciones", "is.null"),
            ],
        )

    def test_column_case_normalization(self) -> None:
        self.session.get.return_value = _mock_response([{"Anio": 2024, "valor_FOB": 1000}])
        # User passes lowercase 'anio' and 'peso_neto' on exportaciones, which has 'Anio' and 'Peso_Neto'
        self.client.query("exportaciones").select("anio", "peso_neto").eq("anio", 2024).raw()
        params = self.session.get.call_args[1]["params"]
        self.assertIn(("select", "Anio,Peso_Neto"), params)
        self.assertIn(("Anio", "eq.2024"), params)

    def test_auto_pagination_uses_composite_key_and_content_range(self) -> None:
        page1 = [{"periodo": "202401", "valor": 1}, {"periodo": "202402", "valor": 2}]
        page2 = [{"periodo": "202403", "valor": 3}]
        self.session.get.side_effect = [
            _mock_response(page1, status_code=206, headers={"Content-Range": "0-1/3"}),
            _mock_response(page2, status_code=206, headers={"Content-Range": "2-2/3"}),
        ]

        qb = self.client.query("canasta_crianza").order("anio.desc")
        resp = qb.execute(fetch_all=True, page_size=2)

        self.assertEqual(len(resp), 3)
        self.assertEqual(resp.total_count, 3)
        self.assertEqual(resp.pages_fetched, 2)

        first_call_params = dict(self.session.get.call_args_list[0][1]["params"])
        # Must include user order 'anio.desc' AND the endpoint's pagination key 'Periodo'
        self.assertEqual(first_call_params["order"], "anio.desc,Periodo")
        self.assertEqual(
            self.session.get.call_args_list[0][1]["headers"].get("Prefer"),
            "count=exact",
        )

    def test_all_19_endpoint_methods_dispatch_correctly(self) -> None:
        self.session.get.return_value = _mock_response([{"ok": 1}])

        method_to_path = {
            "ipi_manufacturero": "/ipi_manufacturero",
            "ipi_minero": "/ipi_minero",
            "estimaciones_poblacion_departamento_2022_2035": "/estimaciones_poblacion_departamento_2022_2035",
            "proyecciones_poblacion_jurisdiccion_2022_2040": "/proyecciones_poblacion_jurisdiccion_2022_2040",
            "proyecciones_poblacion_nacional_2022_2040": "/proyecciones_poblacion_nacional_2022_2040",
            "ipc_nacional": "/ipc_nacional",
            "valorizacion_canastas_cba_cbt": "/valorizacion_canastas_cba_cbt",
            "indice_salarios": "/indice_salarios",
            "icc_precios_construccion": "/icc_precios_construccion",
            "redeterminacion_precios_contratos_obras_publicas": "/redeterminacion_precios_contratos_obras_publicas",
            "sipm_precios_mayoristas": "/sipm_precios_mayoristas",
            "estimador_mensual_de_actividad_economica_nivel_general": "/estimador-mensual-de-actividad-economica-nivel-general",
            "estimador_mensual_de_actividad_economica_sectores": "/estimador-mensual-de-actividad-economica-sectores",
            "pobreza_eph": "/pobreza_eph",
            "mercado_trabajo_eph": "/mercado_trabajo_eph",
            "canasta_crianza": "/canasta-crianza",
            "comercio_exterior_nomenclaturas": "/comercio_exterior_nomenclaturas",
            "comercio_exterior_exportacion_bienes": "/comercio_exterior_exportacion_bienes",
            "comercio_exterior_importacion_bienes": "/comercio_exterior_importacion_bienes",
        }
        self.assertEqual(len(method_to_path), 19)

        for method_name, expected_path in method_to_path.items():
            method = getattr(self.client, method_name)
            res = method(limit=5, as_dataframe=False)
            self.assertEqual(res, [{"ok": 1}])
            called_url = self.session.get.call_args[0][0]
            self.assertEqual(called_url, f"https://api.indec.gob.ar/v1{expected_path}")

    def test_error_handling_postgrest_payload(self) -> None:
        err_payload = {
            "code": "PGRST100",
            "message": '"failed to parse filter (2024)"',
            "details": "unexpected '2'",
            "hint": "Use eq.2024",
        }
        self.session.get.return_value = _mock_response(err_payload, status_code=400)
        with self.assertRaises(IndecFilterError) as ctx:
            self.client.ipc_nacional(anio=2024)
        self.assertEqual(ctx.exception.code, "PGRST100")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.hint, "Use eq.2024")

        self.session.get.return_value = _mock_response({"message": "Invalid JWT"}, status_code=401)
        with self.assertRaises(IndecAuthError):
            self.client.ipc_nacional()

        self.session.get.return_value = _mock_response({"message": "Forbidden"}, status_code=403)
        with self.assertRaises(IndecPermissionError):
            self.client.ipc_nacional()

        self.session.get.return_value = _mock_response({"message": "Rate limit"}, status_code=429)
        with self.assertRaises(IndecRateLimitError):
            self.client.ipc_nacional()

        self.session.get.return_value = _mock_response({"message": "Server error"}, status_code=500)
        with self.assertRaises(IndecAPIError):
            self.client.ipc_nacional()

    def test_catalog_and_signos_convencionales(self) -> None:
        self.assertEqual(len(ENDPOINTS), 19)
        df_ep = list_endpoints(as_dataframe=True)
        self.assertIsInstance(df_ep, pd.DataFrame)
        self.assertEqual(len(df_ep), 19)

        df_cols = describe_endpoint("emae", as_dataframe=True)
        self.assertIsInstance(df_cols, pd.DataFrame)
        self.assertIn("valor", df_cols["columna"].tolist())

        with self.assertRaises(IndecNotFoundError):
            describe_endpoint("endpoint_inexistente")

        self.assertEqual(len(SIGNOS_CONVENCIONALES), 10)
        self.assertEqual(explain_sign("*"), "Dato provisorio")
        self.assertEqual(explain_sign("s"), "Dato confidencial por aplicación de las reglas del secreto estadístico")
        self.assertEqual(parse_content_range("0-999/103545"), (0, 999, 103545))
        self.assertEqual(parse_content_range("*/0"), (None, None, 0))


if __name__ == "__main__":
    unittest.main()
