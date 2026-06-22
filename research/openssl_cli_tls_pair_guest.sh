echo COPPER_OPENSSL_CLI_TLS_PAIR_START
cat > /tmp/copper_tls_pair_ns.sh <<'COPPER_TLS_PAIR_NS'
set -u
echo COPPER_OPENSSL_CLI_TLS_PAIR_NS_ENTER
ip link set lo up
PSK=00112233445566778899aabbccddeeff
server_rc=0
client_rc=0
/usr/bin/openssl s_server -accept 4433 -www -naccept 1 -tls1_2 -nocert -psk_identity copper -psk $PSK > /tmp/ossl_s_server.out 2> /tmp/ossl_s_server.err &
srv=$!
echo COPPER_OPENSSL_CLI_TLS_PAIR_SERVER_PID $srv
printf 'GET / HTTP/1.0\r\n\r\n' | /usr/bin/openssl s_client -connect 127.0.0.1:4433 -tls1_2 -psk_identity copper -psk $PSK -quiet > /tmp/ossl_s_client.out 2> /tmp/ossl_s_client.err || client_rc=$?
echo COPPER_OPENSSL_CLI_TLS_PAIR_CLIENT_DONE rc=$client_rc
if [ $client_rc != 0 ]; then
  kill $srv 2>/dev/null || true
fi
wait $srv || server_rc=$?
echo COPPER_OPENSSL_CLI_TLS_PAIR_SERVER_DONE rc=$server_rc
server_bytes=$(wc -c < /tmp/ossl_s_server.out)
client_bytes=$(wc -c < /tmp/ossl_s_client.out)
server_err_bytes=$(wc -c < /tmp/ossl_s_server.err)
client_err_bytes=$(wc -c < /tmp/ossl_s_client.err)
client_sha=$(/usr/bin/openssl dgst -sha256 /tmp/ossl_s_client.out | sed 's/^.*= //')
server_sha=$(/usr/bin/openssl dgst -sha256 /tmp/ossl_s_server.out | sed 's/^.*= //')
echo COPPER_OPENSSL_CLI_TLS_PAIR_RESULT server_rc=$server_rc client_rc=$client_rc server_bytes=$server_bytes client_bytes=$client_bytes server_err_bytes=$server_err_bytes client_err_bytes=$client_err_bytes client_sha=$client_sha server_sha=$server_sha
cat /tmp/ossl_s_client.err | sed 's/^/COPPER_OPENSSL_CLI_TLS_PAIR_CLIENT_ERR /' | head -20 || true
cat /tmp/ossl_s_server.err | sed 's/^/COPPER_OPENSSL_CLI_TLS_PAIR_SERVER_ERR /' | head -20 || true
if [ $server_rc = 0 ] && [ $client_rc = 0 ]; then exit 0; fi
exit 1
COPPER_TLS_PAIR_NS
chmod +x /tmp/copper_tls_pair_ns.sh
unshare -Urn /bin/sh /tmp/copper_tls_pair_ns.sh
pair_rc=$?
echo COPPER_OPENSSL_CLI_TLS_PAIR_DONE rc=$pair_rc
exit $pair_rc
