from io import BytesIO
from random import randint
from itertools import tee
from PIL import Image


def pairwise(iterable):
    """Awesome function from the itertools cookbook
    https://docs.python.org/2/library/itertools.html
    s -> (s0,s1), (s1,s2), (s2, s3), ...
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class GlitchedImage(object):

    def __init__(self, image_bytes, amount, seed, iterations):
        self.bytes = image_bytes
        self.new_bytes = None
        self.header_length = self.get_header_length()

        self.parameters = {
            'amount': amount,
            'seed': seed,
            'iterations': iterations
        }

        self.glitch_bytes()

    def get_header_length(self):
        """Get the length of the header by searching sequential 0xFF 0xDA
        values. These values mark the end of a Jpeg header. We add two to give
        us a little leeway. We don't want to mess with the header.
        """

        for i, pair in enumerate(pairwise(self.bytes)):
            if pair[0] == 255 and pair[1] == 218:
                result = i + 2
                return result

        raise ValueError('Not a valid jpg!')

    def glitch_bytes(self):
        """Glitch the image bytes, after the header based on the parameters.
        'Amount' is the hex value that will be written into the file. 'Seed'
        tweaks the index where the value will be inserted, rather than just a
        simple division by iterations. 'Iterations' should be self explanatory
        """

        amount = self.parameters['amount'] / 100
        seed = self.parameters['seed'] / 100
        iterations = self.parameters['iterations']

        # work with a copy of the original bytes. We might need the original
        # bytes around if we glitch it so much we break the file.
        new_bytes = self.bytes.copy()

        for i in range(iterations):
            max_index = len(self.bytes) - self.header_length - 4

            # The following operations determine where we'll overwrite a value
            # Illustrate by example

            # 36 = (600 / 50) * 3
            px_min = int((max_index / iterations) * i)

            # 48 = (600 / 50) * 3 + 1
            px_max = int((max_index / iterations) * (i + 1))

            # 12 = 48 - 36
            delta = (px_max - px_min)  # * 0.8

            # 36 + (12 * 0.8)
            px_i = int(px_min + (delta * seed))

            # If the index to be changed is beyond bytearray length file set
            # it to the max index
            if (px_i > max_index):
                px_i = max_index

            byte_index = self.header_length + px_i
            new_bytes[byte_index] = int(amount * 256)

        self.new_bytes = new_bytes

    def save_image(self, name, ext=None):
        """Save the image to a file. Keep trying by re-glitching the image with
        less iterations if it fails
        """

        while True:
            try:
                stream = BytesIO(self.new_bytes)
                im = Image.open(stream)
                im.save(name, ext)
                return
            except IOError:
                if self.parameters['iterations'] == 1:
                    raise Exception('This image is beyond \
                            repair, maybe try again?')

                self.parameters['iterations'] -= 1
                self.glitch_bytes()