import market

u, p, i = ('Storeyle71@gmail.com', 'learnlet49', '37c0f424a35fdf1d')
a = "DQAAAL4AAAA9tSOv_lY4EQ0LLe4fmKVCtbCt7D8CVnGiLAO-gbFO1yZwgHezVWujExEM23ciCxTS-fRCPrhdoNLwEz8B_HV1Gl9qHOvNMOR77cWebK5NS8cUFxzrvaFusrZ7fDxY3l-cEgycuyydTxHtkgrj9awlSwcrBhOAFs4ROT9G1DJPOmiGjdr_PKUWX8d4_slwmnTNg37v_TtgRjpbkSsjfk05l-IhV_yTiuIoeVVBpBrRifsTTS2O960_g9dqT6FYFeM"

m = market.Market(a, i)
m.download("com.zynga.words", "words_app.apk")
print('done')
