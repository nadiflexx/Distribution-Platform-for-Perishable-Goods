from unittest.mock import MagicMock, patch

from distribution_platform.infrastructure.external.geocoding import fetch_coordinates


@patch("distribution_platform.infrastructure.external.geocoding._geolocator")
@patch("distribution_platform.infrastructure.external.geocoding.time.sleep")
class TestGeocoding:
    def test_fetch_coordinates_success(self, mock_sleep, mock_geolocator):
        """Prueba que devuelve lat,lon cuando la API responde a la primera."""
        # Configurar Mock
        mock_location = MagicMock()
        mock_location.latitude = 41.38
        mock_location.longitude = 2.17
        mock_geolocator.geocode.return_value = mock_location

        # Ejecutar
        result = fetch_coordinates("Barcelona")

        # Verificar
        assert result == "41.38,2.17"
        mock_geolocator.geocode.assert_called_once()
        mock_sleep.assert_not_called()

    def test_fetch_coordinates_retry_success(self, mock_sleep, mock_geolocator):
        """
        Prueba que reintenta si falla la primera vez y tiene éxito la segunda.
        """
        # Configurar Mock: Primera llamada lanza error, segunda devuelve objeto
        mock_location = MagicMock()
        mock_location.latitude = 40.0
        mock_location.longitude = -3.0

        # side_effect permite definir una secuencia de respuestas
        mock_geolocator.geocode.side_effect = [Exception("Timeout"), mock_location]

        # Ejecutar
        result = fetch_coordinates("Toledo")

        # Verificar
        assert result == "40.0,-3.0"
        assert mock_geolocator.geocode.call_count == 2
        mock_sleep.assert_called_once()  # Se durmió una vez entre intentos

    def test_fetch_coordinates_fallback(self, mock_sleep, mock_geolocator):
        """
        Prueba que devuelve coordenadas por defecto (Madrid) si agota los intentos.
        """
        # Configurar Mock: Siempre falla
        mock_geolocator.geocode.side_effect = Exception("API Down")

        # Ejecutar
        result = fetch_coordinates("Ciudad Inexistente", max_attempts=3)

        # Verificar Fallback (Madrid)
        assert result == "40.4168,-3.7038"
        assert mock_geolocator.geocode.call_count == 3
