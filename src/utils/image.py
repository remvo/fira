import cv2
from scipy.spatial import distance as dist


def midpoint(point1, point2):
    return (point1[0] + point2[0]) * 0.5, (point1[1] + point2[1]) * 0.5


def get_blurred_image(image):
    # TODO: 설정 화면을 통해서 블러 알고리즘 및 매개변수를 설정할수 있도록 변경
    blurred = cv2.GaussianBlur(image, (13, 13), 0)
    # blurred = cv2.medianBlur(image, 5)
    return blurred


def resize_image(img, width, height, interpolation='INTER_LINEAR'):
    """
    이미지 크기 변경
    :param interpolation: 보간법
                            - INTER_LINEAR: 양선형 보간법(Default)
                            - INTER_AREA: 픽셀 영역 재 샘플링
                            - INTER_NEAREST: 최근방 이웃 보간법
                            - INTER_CUBIC: 3차 회선 보간법
    :param img:
    :param width:
    :param height:
    :return:
    """
    # TODO: 설정 화면을 통해서 선택 가능하도록 변경
    img_height, img_width, img_colors = img.shape
    scale_w = float(width) / float(img_width)
    scale_h = float(height) / float(img_height)
    scale = min([scale_w, scale_h])

    if scale == 0:
        scale = 1

    interpolation = getattr(cv2, interpolation)
    return cv2.resize(img, None, fx=scale, fy=scale, interpolation=interpolation)


def draw_rectangle(img, box, color=(0, 0, 0), width=4, display_info=False):
    if img is None or box is None:
        return img

    # draw
    cv2.polylines(img, [box], True, color, width)

    # loop over the original points and draw them
    for (x, y) in box:
        cv2.circle(img, (int(x), int(y)), 5, (0, 0, 255), -1)

    if display_info:
        # unpack the ordered bounding box, then compute the midpoint
        # between the top-left and top-right coordinates, followed by
        # the midpoint between bottom-left and bottom-right coordinates
        (tl, tr, br, bl) = box
        (tltrX, tltrY) = midpoint(tl, tr)
        (blbrX, blbrY) = midpoint(bl, br)

        # compute the midpoint between the top-left and bottom-left points,
        # followed by the midpoint between the top-right and bottom-right
        (tlblX, tlblY) = midpoint(tl, bl)
        (trbrX, trbrY) = midpoint(tr, br)

        # draw the midpoints on the image
        cv2.circle(img, (int(tltrX), int(tltrY)), 5, (255, 0, 0), -1)
        cv2.circle(img, (int(blbrX), int(blbrY)), 5, (255, 0, 0), -1)
        cv2.circle(img, (int(tlblX), int(tlblY)), 5, (255, 0, 0), -1)
        cv2.circle(img, (int(trbrX), int(trbrY)), 5, (255, 0, 0), -1)

        # draw lines between the midpoints
        cv2.line(img, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)),
                 (255, 0, 255), 2)
        cv2.line(img, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)),
                 (255, 0, 255), 2)

        # compute the Euclidean distance between the midpoints
        dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
        dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))

        # draw the object sizes on the image
        cv2.putText(img, "{}px".format(int(dA)),
                    (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (255, 255, 255), 2)
        cv2.putText(img, "{}px".format(int(dB)),
                    (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (255, 255, 255), 2)

        # draw the object area size on the image
        cv2.putText(img, "size: {}".format(int(dA * dB)),
                    (int(tltrX - 15), int(tltrY - 40)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (255, 255, 255), 2)


def rect_min_dist(rect1, rect2):
    min_dist = 99999

    for point1 in rect1:
        for point2 in rect2:
            cur_dist = dist.euclidean(point1, point2)
            min_dist = cur_dist if cur_dist < min_dist else min_dist

    return min_dist
